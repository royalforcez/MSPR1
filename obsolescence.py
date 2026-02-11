def screen_obsolescence_audit(stdscr):
    stdscr.clear()
    stdscr.addstr(2, 2, "ENTREE DANS LE MODULE OBSOLESCENCE OK")
    stdscr.addstr(4, 2, "Appuie sur une touche")
    stdscr.refresh()
    stdscr.getch()

import curses
import csv
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import requests

# --- Optionnel : accès MySQL (si tu utilises MySQL, ce qui colle à ton projet) ---
# pip install mysql-connector-python
try:
    import mysql.connector
except Exception:
    mysql = None  # si non installé, on gérera proprement

# =========================
# Configuration
# =========================

EOL_API_BASE = "https://endoflife.date/api/v1"  # serveur v1 :contentReference[oaicite:4]{index=4}

OUTPUT_DIR = os.environ.get("OBSO_OUTPUT_DIR", os.path.join("outputs", "obsolescence"))
CACHE_TTL_SECONDS = int(os.environ.get("OBSO_CACHE_TTL_SECONDS", "86400"))  # 24h
SOON_EOL_DAYS = int(os.environ.get("OBSO_SOON_EOL_DAYS", "90"))

# --- BDD (adaptable sans toucher au code) ---
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "mspr")

# Table / colonnes attendues (par défaut) :
# - hostname (ou name)
# - ip (optionnel)
# - os_name
# - os_version
#
# Si ta table n’a pas ces noms, tu peux :
# 1) soit créer une VIEW SQL qui expose ces alias,
# 2) soit modifier la requête SQL ci-dessous.
DEFAULT_DB_QUERY = os.environ.get(
    "OBSO_DB_QUERY",
    """
    SELECT
        hostname,
        ip,
        os_name,
        os_version
    FROM assets
    WHERE os_name IS NOT NULL AND os_version IS NOT NULL
    """
)

# Mapping "os_name" de ta BDD -> "product" endoflife.date
# Adapte-le à ce que tu stockes réellement.
OS_TO_EOL_PRODUCT = {
    "ubuntu": "ubuntu",
    "ubuntu linux": "ubuntu",
    "windows server": "windows-server",
    "windows": "windows",
    "centos": "centos",
    "debian": "debian",
    "rocky": "rocky-linux",
    "alma": "almalinux",
    "esxi": "vmware-esxi",
}

# =========================
# Modèle de données
# =========================

@dataclass
class Asset:
    hostname: str
    ip: Optional[str]
    os_name: str
    os_version: str


@dataclass
class AuditResult:
    hostname: str
    ip: Optional[str]
    os_name: str
    os_version: str
    eol_product: Optional[str]
    matched_cycle: Optional[str]
    eol_date: Optional[str]        # ISO date string
    is_eol: Optional[bool]
    status: str                    # SUPPORTED / SOON_EOL / EOL / UNKNOWN
    days_to_eol: Optional[int]
    notes: str


# =========================
# Utilitaires généraux
# =========================

def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def now_ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def parse_iso_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return None


def normalize(s: str) -> str:
    return " ".join((s or "").strip().lower().replace("_", " ").split())


def version_major_minor(v: str) -> str:
    """
    endoflife.date stocke souvent des cycles type '20.04' (Ubuntu) et pas '20.04.6'.
    On garde donc major.minor si possible.
    """
    v = (v or "").strip()
    parts = v.split(".")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{parts[0]}.{parts[1]}"
    return v


# =========================
# Client endoflife.date + cache simple
# =========================

class EOLClient:
    def __init__(self) -> None:
        ensure_output_dir()
        self.cache_path = os.path.join(OUTPUT_DIR, "eol_cache.json")
        self._cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _is_fresh(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry:
            return False
        fetched_at = entry.get("_fetched_at_epoch")
        if not isinstance(fetched_at, (int, float)):
            return False
        return (time.time() - fetched_at) < CACHE_TTL_SECONDS

    def get_product(self, product: str) -> Dict[str, Any]:
        """
        GET /products/{product} :contentReference[oaicite:5]{index=5}
        """
        product = normalize(product)
        cache_key = f"product:{product}"
        if self._is_fresh(cache_key):
            return self._cache[cache_key]["data"]

        url = f"{EOL_API_BASE}/products/{product}"
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"API endoflife: HTTP {r.status_code} sur {url}")

        data = r.json()
        self._cache[cache_key] = {
            "_fetched_at_epoch": int(time.time()),
            "data": data,
        }
        self._save_cache()
        return data

    def list_releases(self, product: str) -> List[Dict[str, Any]]:
        data = self.get_product(product)
        # Réponse type ProductResponse, champ "result.releases" :contentReference[oaicite:6]{index=6}
        return (data.get("result") or {}).get("releases") or []


# =========================
# Lecture BDD / CSV
# =========================

def fetch_assets_from_db() -> List[Asset]:
    if mysql.connector is None:
        raise RuntimeError(
            "mysql-connector-python n'est pas installé. Fais: pip install mysql-connector-python"
        )

    conn = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    try:
        cur = conn.cursor()
        cur.execute(DEFAULT_DB_QUERY)
        rows = cur.fetchall()
    finally:
        try:
            conn.close()
        except Exception:
            pass

    assets: List[Asset] = []
    for row in rows:
        # On suppose l’ordre hostname, ip, os_name, os_version (cf requête)
        hostname, ip, os_name, os_version = row
        assets.append(
            Asset(
                hostname=str(hostname),
                ip=str(ip) if ip is not None else None,
                os_name=str(os_name),
                os_version=str(os_version),
            )
        )
    return assets


def read_assets_from_csv(path: str) -> List[Asset]:
    """
    CSV attendu (en-têtes) : hostname,ip,os_name,os_version
    """
    assets: List[Asset] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line in reader:
            assets.append(
                Asset(
                    hostname=(line.get("hostname") or "").strip(),
                    ip=(line.get("ip") or "").strip() or None,
                    os_name=(line.get("os_name") or "").strip(),
                    os_version=(line.get("os_version") or "").strip(),
                )
            )
    return assets


# =========================
# Logique audit
# =========================

def map_os_to_product(os_name: str) -> Optional[str]:
    key = normalize(os_name)
    # match direct
    if key in OS_TO_EOL_PRODUCT:
        return OS_TO_EOL_PRODUCT[key]

    # match "contient"
    for k, v in OS_TO_EOL_PRODUCT.items():
        if k in key:
            return v

    return None


def pick_release_cycle(releases: List[Dict[str, Any]], os_version: str) -> Optional[Dict[str, Any]]:
    """
    Cherche un cycle dont le champ 'name' correspond à la version (ou major.minor).
    Exemple Ubuntu: '20.04.6' -> cycle '20.04'
    """
    target = normalize(os_version)
    target_mm = normalize(version_major_minor(os_version))

    # match exact d'abord
    for rel in releases:
        if normalize(str(rel.get("name", ""))) == target:
            return rel

    # match major.minor ensuite
    for rel in releases:
        if normalize(str(rel.get("name", ""))) == target_mm:
            return rel

    return None


def compute_status(eol_from: Optional[date]) -> Tuple[str, Optional[int]]:
    """
    Statut basé sur la date EOL.
    - UNKNOWN si pas de date
    - EOL si passé
    - SOON_EOL si <= SOON_EOL_DAYS
    - SUPPORTED sinon
    """
    if eol_from is None:
        return "UNKNOWN", None

    today = date.today()
    delta = (eol_from - today).days

    if delta < 0:
        return "EOL", delta
    if delta <= SOON_EOL_DAYS:
        return "SOON_EOL", delta
    return "SUPPORTED", delta


def audit_assets(assets: List[Asset], client: EOLClient) -> List[AuditResult]:
    results: List[AuditResult] = []

    for a in assets:
        product = map_os_to_product(a.os_name)
        if not product:
            results.append(
                AuditResult(
                    hostname=a.hostname,
                    ip=a.ip,
                    os_name=a.os_name,
                    os_version=a.os_version,
                    eol_product=None,
                    matched_cycle=None,
                    eol_date=None,
                    is_eol=None,
                    status="UNKNOWN",
                    days_to_eol=None,
                    notes="OS non mappé vers endoflife.date (ajoute-le dans OS_TO_EOL_PRODUCT).",
                )
            )
            continue

        try:
            releases = client.list_releases(product)
            rel = pick_release_cycle(releases, a.os_version)

            if not rel:
                results.append(
                    AuditResult(
                        hostname=a.hostname,
                        ip=a.ip,
                        os_name=a.os_name,
                        os_version=a.os_version,
                        eol_product=product,
                        matched_cycle=None,
                        eol_date=None,
                        is_eol=None,
                        status="UNKNOWN",
                        days_to_eol=None,
                        notes="Version/cycle introuvable sur endoflife.date pour ce produit.",
                    )
                )
                continue

            eol_date_str = rel.get("eolFrom")  # champ défini dans ProductRelease :contentReference[oaicite:7]{index=7}
            eol_dt = parse_iso_date(eol_date_str)
            status, days = compute_status(eol_dt)

            results.append(
                AuditResult(
                    hostname=a.hostname,
                    ip=a.ip,
                    os_name=a.os_name,
                    os_version=a.os_version,
                    eol_product=product,
                    matched_cycle=str(rel.get("name")),
                    eol_date=eol_date_str,
                    is_eol=bool(rel.get("isEol")) if rel.get("isEol") is not None else None,
                    status=status,
                    days_to_eol=days,
                    notes="OK",
                )
            )

        except Exception as e:
            results.append(
                AuditResult(
                    hostname=a.hostname,
                    ip=a.ip,
                    os_name=a.os_name,
                    os_version=a.os_version,
                    eol_product=product,
                    matched_cycle=None,
                    eol_date=None,
                    is_eol=None,
                    status="UNKNOWN",
                    days_to_eol=None,
                    notes=f"Erreur API: {e}",
                )
            )

    return results


# =========================
# Export / Rapport
# =========================

def write_report_json(results: List[AuditResult]) -> str:
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, f"report_{now_ts()}.json")
    payload = {
        "generated_at": datetime.now().isoformat(),
        "soon_eol_days_threshold": SOON_EOL_DAYS,
        "counts": {
            "total": len(results),
            "SUPPORTED": sum(1 for r in results if r.status == "SUPPORTED"),
            "SOON_EOL": sum(1 for r in results if r.status == "SOON_EOL"),
            "EOL": sum(1 for r in results if r.status == "EOL"),
            "UNKNOWN": sum(1 for r in results if r.status == "UNKNOWN"),
        },
        "results": [asdict(r) for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def write_report_csv(results: List[AuditResult]) -> str:
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, f"report_{now_ts()}.csv")
    fields = [
        "hostname", "ip", "os_name", "os_version",
        "eol_product", "matched_cycle", "eol_date", "is_eol",
        "status", "days_to_eol", "notes"
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            w.writerow(asdict(r))
    return path


# =========================
# UI curses (intégration)
# =========================

def _curses_prompt(stdscr, y: int, x: int, prompt: str) -> str:
    """
    Affiche un prompt et lit une saisie utilisateur.
    """
    stdscr.addstr(y, x, prompt)
    stdscr.clrtoeol()
    curses.echo()
    s = stdscr.getstr(y, x + len(prompt), 120).decode("utf-8", errors="ignore")
    curses.noecho()
    return s.strip()


def _draw_box(stdscr, title: str, lines: List[str]) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(2, (w - len(title)) // 2, title)
    stdscr.attroff(curses.color_pair(3))

    y = 4
    for line in lines[: h - 7]:
        stdscr.addstr(y, 2, line[: w - 4])
        y += 1

    stdscr.addstr(h - 2, 2, "Appuie sur une touche pour continuer")
    stdscr.refresh()
    stdscr.getch()


def screen_obsolescence_audit(stdscr):
    """
    Menu interactif du module obsolescence (appelé depuis ton menu principal).
    """
    client = EOLClient()
    last_results: List[AuditResult] = []

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        title = "Module Audit d’Obsolescence"
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3))

        menu = [
            "1) Lister les cycles/versions + EOL d'un OS (endoflife.date)",
            "2) Lancer un audit depuis la BDD (machines stockées)",
            "3) Lancer un audit depuis un CSV (hostname,ip,os_name,os_version)",
            "4) Exporter le dernier audit en CSV",
            "0) Retour",
        ]
        y0 = 5
        for i, item in enumerate(menu):
            stdscr.addstr(y0 + i, 4, item)

        choice = _curses_prompt(stdscr, y0 + len(menu) + 2, 4, "Choix: ")

        if choice == "0":
            return

        # 1) Lister versions / EOL d’un OS
        if choice == "1":
            product = _curses_prompt(stdscr, y0 + len(menu) + 4, 4, "Produit endoflife (ex: ubuntu, windows-server): ")
            try:
                releases = client.list_releases(product)
                lines = [f"{product} : {len(releases)} cycles trouvés", "-" * 60]
                for rel in releases[: min(len(releases), 30)]:
                    lines.append(
                        f"- {rel.get('name')} | EOL: {rel.get('eolFrom')} | Maintained: {rel.get('isMaintained')} | isEol: {rel.get('isEol')}"
                    )
                if len(releases) > 30:
                    lines.append("... (limité à 30 lignes à l'écran)")
                _draw_box(stdscr, "Cycles/versions + EOL", lines)
            except Exception as e:
                _draw_box(stdscr, "Erreur", [str(e)])

        # 2) Audit depuis BDD
        elif choice == "2":
            try:
                assets = fetch_assets_from_db()
                last_results = audit_assets(assets, client)
                json_path = write_report_json(last_results)
                csv_path = write_report_csv(last_results)

                counts = {
                    "SUPPORTED": sum(1 for r in last_results if r.status == "SUPPORTED"),
                    "SOON_EOL": sum(1 for r in last_results if r.status == "SOON_EOL"),
                    "EOL": sum(1 for r in last_results if r.status == "EOL"),
                    "UNKNOWN": sum(1 for r in last_results if r.status == "UNKNOWN"),
                }
                lines = [
                    f"Audit terminé sur {len(assets)} machine(s).",
                    f"SUPPORTED={counts['SUPPORTED']} | SOON_EOL={counts['SOON_EOL']} | EOL={counts['EOL']} | UNKNOWN={counts['UNKNOWN']}",
                    "",
                    f"Rapport JSON : {json_path}",
                    f"Export CSV  : {csv_path}",
                ]
                _draw_box(stdscr, "Audit BDD - Résumé", lines)
            except Exception as e:
                _draw_box(stdscr, "Erreur audit BDD", [str(e)])

        # 3) Audit depuis CSV
        elif choice == "3":
            path = _curses_prompt(stdscr, y0 + len(menu) + 4, 4, "Chemin CSV: ")
            try:
                assets = read_assets_from_csv(path)
                last_results = audit_assets(assets, client)
                json_path = write_report_json(last_results)
                csv_path = write_report_csv(last_results)
                _draw_box(
                    stdscr,
                    "Audit CSV - OK",
                    [
                        f"Audit terminé sur {len(assets)} machine(s).",
                        f"Rapport JSON : {json_path}",
                        f"Export CSV  : {csv_path}",
                    ],
                )
            except Exception as e:
                _draw_box(stdscr, "Erreur audit CSV", [str(e)])

        # 4) Exporter dernier audit
        elif choice == "4":
            if not last_results:
                _draw_box(stdscr, "Export CSV", ["Aucun audit en mémoire. Lance d'abord 2) ou 3)."])
            else:
                try:
                    csv_path = write_report_csv(last_results)
                    _draw_box(stdscr, "Export CSV", [f"Export OK : {csv_path}"])
                except Exception as e:
                    _draw_box(stdscr, "Erreur export", [str(e)])

        else:
            _draw_box(stdscr, "Choix invalide", ["Réessaie."])
