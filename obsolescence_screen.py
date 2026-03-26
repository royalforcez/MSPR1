import curses
import ipaddress
import os
import csv
import re
from datetime import datetime

from session_manager import get_db_connection_ntl
from obsolescence.eol_api import EOLClient


EXPORT_DIR = "exports"


# =====================================================
# EXPORT CSV
# =====================================================

def export_csv(data, source):

    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_{source}_{timestamp}.csv"
    path = os.path.join(EXPORT_DIR, filename)

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Hostname", "IP", "OS", "Version", "EOL", "Statut"])

        for row in data:
            writer.writerow(row)

    return path


# =====================================================
# STATUT EOL
# =====================================================

def get_status(eol_date):

    if not eol_date or eol_date == "N/A":
        return "INCONNU"

    try:
        if isinstance(eol_date, str):
            eol = datetime.strptime(eol_date, "%Y-%m-%d")
        else:
            eol = eol_date

        today = datetime.today()
        diff = (eol - today).days

        if diff < 0:
            return "OBSOLETE"

        if diff < 365:
            return "EOL < 1 AN"

        return "SUPPORTE"

    except Exception:
        return "INCONNU"


# =====================================================
# NORMALISATION OS / VERSION
# =====================================================

def normalize_os(os_name):

    if not os_name:
        return None

    os_name = os_name.lower()

    if "debian" in os_name:
        return "debian"

    if "ubuntu" in os_name:
        return "ubuntu"

    if "windows server" in os_name:
        return "windows-server"

    return None


def normalize_version(version, os_name=None):

    if not version:
        return None

    if os_name and "windows server" in os_name.lower():
        match = re.search(r"\b(20\d{2})\b", os_name)
        if match:
            return match.group(1)

    version = str(version).strip()

    if "." in version:
        return version.split(".")[0]

    return version


def extract_eol_date(release):

    eol = release.get("eol")

    if isinstance(eol, dict):
        return eol.get("date", "N/A")

    if isinstance(eol, str):
        return eol

    return (
        release.get("eolFrom")
        or release.get("eolDate")
        or release.get("extendedSupport")
        or "N/A"
    )


# =====================================================
# FETCH BDD
# =====================================================

def fetch_all_assets():

    conn = get_db_connection_ntl()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.nom,
            e.ipv4,
            o.nom_os,
            o.version_os,
            el.date_expiration
        FROM tb_equipements e
        JOIN tb_os o ON e.id_os = o.id
        LEFT JOIN tb_end_of_life el ON o.id = el.id_os
        WHERE e.est_actif = 1
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# =====================================================
# LECTURE CSV
# =====================================================

def read_assets_from_csv(path):

    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    assets = []

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_fields = ["hostname", "ip", "os_name", "os_version"]

        if not reader.fieldnames:
            raise ValueError("CSV vide ou mal formaté")

        missing = [field for field in required_fields if field not in reader.fieldnames]
        if missing:
            raise ValueError(
                f"Colonnes manquantes : {missing} | Attendu : {required_fields}"
            )

        for line in reader:
            assets.append({
                "hostname": (line.get("hostname") or "UNKNOWN").strip(),
                "ip": (line.get("ip") or "").strip(),
                "os_name": (line.get("os_name") or "UNKNOWN").strip(),
                "os_version": (line.get("os_version") or "UNKNOWN").strip()
            })

    return assets


# =====================================================
# AUDIT CSV
# =====================================================

def audit_csv_assets(assets, client):

    results = []

    for asset in assets:

        hostname = asset["hostname"]
        ip = asset["ip"]
        os_name = asset["os_name"]
        os_version = asset["os_version"]

        try:
            product = normalize_os(os_name)

            if not product:
                results.append([
                    hostname,
                    ip,
                    os_name,
                    os_version,
                    "N/A",
                    "INCONNU"
                ])
                continue

            releases = client.list_releases(product)
            normalized_version = normalize_version(os_version, os_name)

            matched = None

            for release in releases:
                cycle = str(release.get("cycle") or release.get("name") or "")
                if cycle == normalized_version:
                    matched = release
                    break

            if not matched:
                results.append([
                    hostname,
                    ip,
                    os_name,
                    os_version,
                    "N/A",
                    "INCONNU"
                ])
                continue

            eol = extract_eol_date(matched)
            status = get_status(eol)

            results.append([
                hostname,
                ip,
                os_name,
                os_version,
                eol,
                status
            ])

        except Exception:
            results.append([
                hostname,
                ip,
                os_name,
                os_version,
                "N/A",
                "INCONNU"
            ])

    return results


# =====================================================
# FILTRAGE RESEAU
# =====================================================

def filter_by_network(network_cidr, rows):

    network = ipaddress.ip_network(network_cidr, strict=False)

    return [
        r for r in rows
        if r[1] and ipaddress.ip_address(r[1]) in network
    ]


# =====================================================
# INTERFACE PRINCIPALE
# =====================================================

def screen_obsolescence_audit(stdscr):

    stdscr.keypad(True)

    client = EOLClient()
    current = 0

    MODULES = [
        "Lister les versions d’un OS et leurs dates de fin de vie",
        "Lister les composants d’une plage réseau",
        "Lancer un audit depuis la base de données",
        "Lancer un audit depuis un fichier CSV",
        "Retour au menu principal"
    ]

    while True:

        stdscr.clear()

        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

        h, w = stdscr.getmaxyx()

        title = "Module Audit d’Obsolescence"

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3))

        # MENU
        for i, module in enumerate(MODULES):

            cp = curses.color_pair(2 if i == current else 1)

            stdscr.attrset(cp)

            if i == current:
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(6 + i, 4, f"> {module}")
                stdscr.attroff(curses.A_BOLD)
            else:
                stdscr.addstr(6 + i, 4, f"  {module}")

        footer = "↑ ↓ naviguer | ENTER sélectionner | ESC retour"
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        stdscr.refresh()

        key = stdscr.getch()

        # NAVIGATION
        if key == curses.KEY_UP and current > 0:
            current -= 1

        elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
            current += 1

        elif key in (10, 13, curses.KEY_ENTER):

            # =====================================================
            # 1. API EOL DIRECT
            # =====================================================
            if current == 0:

                stdscr.clear()

                label = "Produit (ex: ubuntu, debian, windows-server): "
                stdscr.addstr(5, 4, label)

                curses.echo()
                stdscr.move(5, 4 + len(label))
                product = stdscr.getstr().decode().strip().lower()
                curses.noecho()

                try:
                    releases = client.list_releases(product)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Versions pour {product} :")
                    stdscr.addstr(5, 4, "VERSION        EOL DATE        STATUT")

                    line = 7

                    for r in releases:
                        version = r.get("cycle") or r.get("name") or "N/A"
                        eol = extract_eol_date(r)
                        status = get_status(eol)

                        text = f"{version:<15} {eol:<15} {status}"

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    stdscr.addstr(h - 1, 2, "ESC: retour")

                    while stdscr.getch() != 27:
                        pass

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur API : {e}")
                    stdscr.getch()

            # =====================================================
            # 2. RESEAU (BDD + EXPORT)
            # =====================================================
            elif current == 1:

                stdscr.clear()

                label = "Réseau CIDR (ex: 192.168.1.0/24) : "
                stdscr.addstr(5, 4, label)

                curses.echo()
                stdscr.move(5, 4 + len(label))
                network = stdscr.getstr().decode().strip()
                curses.noecho()

                try:
                    rows = fetch_all_assets()
                    filtered = filter_by_network(network, rows)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Machines dans {network} :")
                    stdscr.addstr(5, 4, "HOSTNAME        IP              OS              VERSION")

                    line = 7
                    display_data = []

                    for r in filtered:
                        hostname, ip, os_name, version, _ = r

                        text = f"{hostname:<15} {ip:<15} {os_name:<20} {version}"

                        display_data.append([hostname, ip, os_name, version, "", ""])

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    if not filtered:
                        stdscr.addstr(7, 4, "Aucun équipement trouvé.")

                    footer = "F3: Export CSV | ESC: retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3 and filtered:
                            path = export_csv(display_data, "network")

                            msg = f"Export : {path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur BDD : {e}")
                    stdscr.getch()

            # =====================================================
            # 3. AUDIT BDD + EXPORT
            # =====================================================
            elif current == 2:

                stdscr.clear()
                stdscr.addstr(5, 4, "Audit en cours (BDD)...")
                stdscr.refresh()

                try:
                    rows = fetch_all_assets()

                    stdscr.clear()
                    stdscr.addstr(3, 4, "Résultat audit :")
                    stdscr.addstr(5, 4, "HOSTNAME        IP              OS              VERSION     EOL         STATUT")

                    line = 7
                    display_data = []

                    for r in rows:
                        hostname, ip, os_name, version, eol = r

                        status = get_status(eol)
                        eol_str = str(eol) if eol else "N/A"

                        text = f"{hostname:<15} {ip:<15} {os_name:<20} {version:<10} {eol_str:<12} {status}"

                        display_data.append([hostname, ip, os_name, version, eol_str, status])

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    footer = "F3: Export CSV | ESC: retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3:
                            path = export_csv(display_data, "db")

                            msg = f"Export : {path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur BDD : {e}")
                    stdscr.getch()

            # =====================================================
            # 4. AUDIT CSV + EXPORT
            # =====================================================
            elif current == 3:

                stdscr.clear()
                stdscr.addstr(5, 4, "Chemin CSV : ")

                curses.echo()
                stdscr.move(5, 17)
                stdscr.clrtoeol()
                path = stdscr.getstr().decode("utf-8").strip()
                curses.noecho()

                try:
                    assets = read_assets_from_csv(path)
                    results = audit_csv_assets(assets, client)

                    stdscr.clear()
                    stdscr.addstr(3, 4, "Résultat audit CSV :")
                    stdscr.addstr(5, 4, "HOSTNAME        IP              OS              VERSION     EOL         STATUT")

                    line = 7
                    display_data = []

                    for row in results:
                        hostname, ip, os_name, version, eol, status = row

                        text = f"{hostname:<15} {ip:<15} {os_name:<20} {version:<10} {eol:<12} {status}"

                        display_data.append([hostname, ip, os_name, version, eol, status])

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    footer = "F3: Export CSV | ESC: retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3 and display_data:
                            export_path = export_csv(display_data, "csv")

                            msg = f"Export : {export_path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur CSV : {e}")
                    stdscr.getch()

            # =====================================================
            # RETOUR
            # =====================================================
            elif current == 4:
                return

        elif key == 27:
            return