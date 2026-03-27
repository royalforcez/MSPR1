import curses
import ipaddress
import os
import csv
import re
from datetime import datetime
import logging

from session_manager import get_db_connection_ntl
from obsolescence.eol_api import EOLClient


EXPORT_DIR = "exports"

# =====================================================
# EXPORT JSON
# =====================================================

def export_json(data, prefix="audit"):

    target_dir = EXPORT_DIR

    try:
        os.makedirs(target_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(target_dir, filename)

        if not data:
            logging.warning("Export JSON : Aucune donnée à exporter.")
            return None

        json_data = []

        for row in data:
            json_data.append({
                "hostname": row[0],
                "ip": row[1],
                "os": row[2],
                "version": row[3],
                "eol_date": row[4],
                "status": row[5]
            })

        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        return filepath

    except Exception as e:
        logging.error(f"Erreur export JSON : {e}")
        return None

# =====================================================
# STATUT EOL
# =====================================================

def get_status(eol_date):

    if not eol_date or eol_date == "N/A":
        return "INCONNU"

    try:
        today = datetime.today().date()

        # Si string → conversion
        if isinstance(eol_date, str):
            eol = datetime.strptime(eol_date, "%Y-%m-%d").date()

        # Si déjà date → OK
        else:
            eol = eol_date

        diff = (eol - today).days

        if diff < 0:
            return "OBSOLETE"

        if diff < 365:
            return "EOL < 1 AN"

        return "SUPPORTE"

    except Exception as e:
        return "INCONNU"


# =====================================================
# NORMALISATION
# =====================================================

def normalize_os(os_name):
    if not os_name:
        return None

    os_name = os_name.lower()

    if "debian" in os_name: return "debian"
    if "ubuntu" in os_name: return "ubuntu"
    if "windows server" in os_name: return "windows-server"

    return None


def normalize_version(version, os_name=None):
    if not version:
        return None

    try:
        if os_name and "windows server" in os_name.lower():
            match = re.search(r"\b(20\d{2})\b", os_name)
            if match:
                return match.group(1)

        version = str(version).strip()
        if "." in version:
            return version.split(".")[0]
        return version

    except:
        return None


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
# BDD
# =====================================================

def fetch_all_assets():
    try:
        conn = get_db_connection_ntl()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                e.nom, e.ipv4, o.nom_os, o.version_os, el.date_expiration
            FROM tb_equipements e
            JOIN tb_os o ON e.id_os = o.id
            LEFT JOIN tb_end_of_life el ON o.id = el.id_os
            WHERE e.est_actif = 1
        """)

        rows = cursor.fetchall()
        conn.close()

        return rows

    except Exception as e:
        logging.error(f"Erreur BDD : {e}")
        raise ValueError("Impossible de se connecter à la base de données")


# =====================================================
# CSV
# =====================================================

def read_assets_from_csv(path):

    assets = []

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for line in reader:
            assets.append({
                "hostname": line["hostname"],
                "ip": line["ip"],
                "os_name": line["os_name"],
                "os_version": line["os_version"]
            })

    return assets


def audit_csv_assets(assets, client):

    results = []

    for asset in assets:
        h, ip = asset["hostname"], asset["ip"]
        os_n, os_v = asset["os_name"], asset["os_version"]

        product = normalize_os(os_n)

        if not product:
            results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])
            continue

        try:
            releases = client.list_releases(product)
            normalized_v = normalize_version(os_v, os_n)

            matched = next(
                (r for r in releases if str(r.get("cycle") or r.get("name")) == normalized_v),
                None
            )

            if not matched:
                results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])
                continue

            eol = extract_eol_date(matched)
            status = get_status(eol)

            results.append([h, ip, os_n, os_v, eol, status])

        except:
            results.append([h, ip, os_n, os_v, "N/A", "INCONNU"])

    return results


# =====================================================
# RESEAU
# =====================================================

def filter_by_network(network_cidr, rows):

    network = ipaddress.ip_network(network_cidr, strict=False)

    return [
        r for r in rows
        if r[1] and ipaddress.ip_address(r[1]) in network
    ]


# =====================================================
# UI EXPORT (CENTRALISÉ)
# =====================================================

def wait_with_export(stdscr, results, prefix):

    h, w = stdscr.getmaxyx()

    stdscr.addstr(h - 2, 4, "F3 : Export JSON | ESC : Retour")
    stdscr.refresh()

    key = stdscr.getch()

    if key == curses.KEY_F3:
        path = export_json(results, prefix)

        if path:
            stdscr.addstr(h - 3, 4, f"Export : {path}", curses.color_pair(2))
        else:
            stdscr.addstr(h - 3, 4, "Erreur export", curses.color_pair(1))

        stdscr.getch()

    elif key == 27:
        return

    else:
        return

# =====================================================
# INPUT UTILISATEUR (PROPRE)
# =====================================================

def get_input(stdscr, y, x, label, max_length=50):

    stdscr.addstr(y, x, label)

    # position dynamique après le texte
    x_input = x + len(label)

    curses.echo()
    stdscr.move(y, x_input)
    value = stdscr.getstr(y, x_input, max_length).decode().strip()
    curses.noecho()

    return value

# =====================================================
# INTERFACE
# =====================================================

def screen_obsolescence_audit(stdscr):

    stdscr.keypad(True)
    curses.curs_set(0)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)

    client = EOLClient()
    current_row = 0

    MODULES = [
        "Lister les versions d’un OS et leurs dates de fin de vie",
        "Lister les composants d’une plage réseau",
        "Lancer un audit depuis la base de données",
        "Lancer un audit depuis un fichier CSV",
        "Retour au menu principal"
    ]

    while True:

        stdscr.clear()
        h, w = stdscr.getmaxyx()

        title = "--- MODULE AUDIT D'OBSOLESCENCE ---"
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        for i, module in enumerate(MODULES):

            if i == current_row:
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(6 + i, 4, f" > {module}")
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            else:
                stdscr.addstr(6 + i, 4, f"   {module}")

        stdscr.addstr(h - 1, (w - 40) // 2, "↑/↓ : Naviguer | ENTER : Sélectionner | ESC : Retour")

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1

        elif key == curses.KEY_DOWN and current_row < len(MODULES) - 1:
            current_row += 1

        elif key == 27:
            return

        elif key in (10, 13):

            # API
            if current_row == 0:

                stdscr.clear()

                product = get_input(stdscr,5,4,"Produit (ex: ubuntu, debian, windows-server): ")    

                try:
                    releases = client.list_releases(product)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Versions pour {product}")
                    stdscr.addstr(5, 4, "VERSION        EOL DATE        STATUT")

                    for i, r in enumerate(releases):
                        if 7 + i >= h - 2:
                            break
                        version = r.get("cycle") or r.get("name")
                        eol = extract_eol_date(r)
                        status = get_status(eol)
                        stdscr.addstr(7 + i, 4, f"{version:<15} {eol:<15} {status}")

                    stdscr.getch()

                except:
                    stdscr.addstr(7, 4, "Erreur API")
                    stdscr.getch()

            # RESEAU
            elif current_row == 1:

                stdscr.clear()

                cidr = get_input(stdscr,5,4,"Réseau CIDR (ex: 192.168.1.0/24): ")
                try:
                    rows = fetch_all_assets()
                except ValueError as e:
                    stdscr.addstr(7, 4, str(e), curses.color_pair(1))
                    stdscr.addstr(9, 4, "Appuyez sur une touche...")
                    stdscr.getch()
                    continue
                filtered = filter_by_network(cidr, rows)

                results = [[r[0], r[1], r[2], r[3], "N/A", "INCONNU"] for r in filtered]

                stdscr.clear()
                stdscr.addstr(3, 4, f"Résultats {cidr}")
                stdscr.addstr(5, 4, f"{'HOSTNAME':<20} {'IP':<18} {'OS':<25} {'VERSION':<10}")

                for i, r in enumerate(results):
                    if 7 + i >= h - 3:
                        break
                    hostname = r[0]
                    ip = r[1]
                    os_name = r[2]
                    version = r[3]

                    stdscr.addstr(7 + i, 4, f"{hostname:<20} {ip:<18} {os_name:<25} {version:<10}")

                wait_with_export(stdscr, results, "network")

            # AUDIT BDD
            elif current_row == 2:

                stdscr.clear()
                stdscr.addstr(5, 4, "Audit en cours...")
                stdscr.refresh()
                
                try:
                    data = fetch_all_assets()
                except ValueError as e:
                    stdscr.clear()
                    stdscr.addstr(5, 4, str(e), curses.color_pair(1))
                    stdscr.addstr(7, 4, "Appuyez sur une touche...")
                    stdscr.getch()
                    continue

                results = [[r[0], r[1], r[2], r[3], str(r[4]), get_status(r[4])] for r in data]

                stdscr.clear()
                stdscr.addstr(3, 4, "Résultat audit")
                stdscr.addstr(5, 4, f"{'HOSTNAME':<20} {'IP':<18} {'OS':<25} {'VERSION':<10} {'EOL DATE':<12} {'STATUT':<12}")

                for i, r in enumerate(results):
                    if 7 + i >= h - 3:
                        break
                    hostname = r[0]
                    ip = r[1]
                    os_name = r[2]
                    version = r[3]
                    eol = r[4]
                    status = r[5]

                    stdscr.addstr(7 + i, 4, f"{hostname:<20} {ip:<18} {os_name:<25} {version:<10} {eol:<12} {status:<12}")

                wait_with_export(stdscr, results, "db_audit")

            # AUDIT CSV
            elif current_row == 3:

                stdscr.clear()

                stdscr.addstr(3, 4, "Audit depuis fichier CSV")

                stdscr.addstr(5, 4, "Format attendu : CSV avec entêtes obligatoires")
                stdscr.addstr(6, 4, "hostname, ip, os_name, os_version")
                stdscr.addstr(7, 4, "Ex : srv-01,192.168.1.10,ubuntu,20.04")

                path = get_input(stdscr, 9, 4, "Chemin CSV : ")

                try:
                    assets = read_assets_from_csv(path)

                    if not assets:
                        raise ValueError("Aucune donnée valide dans le fichier")

                except ValueError as e:
                    stdscr.addstr(11, 4, f"Erreur : {str(e)}", curses.color_pair(1))
                    stdscr.addstr(13, 4, "Appuyez sur une touche pour continuer")
                    stdscr.getch()
                    continue

                except Exception:
                    stdscr.addstr(11, 4, "Erreur inattendue lors de la lecture du CSV", curses.color_pair(1))
                    stdscr.addstr(13, 4, "Appuyez sur une touche pour continuer")
                    stdscr.getch()
                    continue

                results = audit_csv_assets(assets, client)

                stdscr.clear()
                stdscr.addstr(3, 4, "Résultat audit CSV")

                stdscr.addstr(
                    5,
                    4,
                    f"{'HOSTNAME':<20} {'IP':<18} {'OS':<25} {'VERSION':<10} {'EOL DATE':<12} {'STATUT':<12}"
                )

                stdscr.addstr(6, 4, "-" * 100)

                for i, r in enumerate(results):
                    if 8 + i >= h - 3:
                        break

                    stdscr.addstr(
                        8 + i,
                        4,
                        f"{r[0]:<20} {r[1]:<18} {r[2]:<25} {r[3]:<10} {r[4]:<12} {r[5]:<12}"
                    )

                wait_with_export(stdscr, results, "csv_audit")

            elif current_row == 4:
                return