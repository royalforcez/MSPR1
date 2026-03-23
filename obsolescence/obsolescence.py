import curses
import ipaddress
from datetime import datetime
from .eol_api import EOLClient
from .audit_db import fetch_assets_from_db
from .audit_csv import read_assets_from_csv
from .audit_engine import audit_assets
from .reports import write_report_csv, write_report_json


MODULES = [
    "Lister les versions d’un OS et leurs dates de fin de vie",
    "Lister les composants d’une plage réseau",
    "Lancer un audit depuis la base de données",
    "Lancer un audit depuis un fichier CSV",
    "Exporter le résultat du dernier audit",
    "Retour au menu principal"
]


# =====================================================
# STATUT EOL
# =====================================================

def get_status(eol_date):

    if not eol_date or eol_date == "N/A":
        return "INCONNU"

    try:
        today = datetime.today()
        eol = datetime.strptime(eol_date, "%Y-%m-%d")

        diff = (eol - today).days

        if diff < 0:
            return "OBSOLETE"

        if diff < 365:
            return "EOL < 1 AN"

        return "SUPPORTE"

    except Exception:
        return "INCONNU"


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
# FILTRAGE RESEAU (CIDR STRICT)
# =====================================================

def get_assets_in_network(network_cidr, assets):
    """
    Filtrage strict basé sur CIDR
    ex: 192.168.1.0/24
    """

    try:
        network = ipaddress.ip_network(network_cidr, strict=False)
    except ValueError:
        raise ValueError("Format invalide (ex: 192.168.1.0/24)")

    filtered = []

    for asset in assets:
        try:
            if asset.ip:
                ip_obj = ipaddress.ip_address(asset.ip)

                if ip_obj in network:
                    filtered.append(asset)

        except ValueError:
            continue

    return filtered


# =====================================================
# INTERFACE PRINCIPALE
# =====================================================

def screen_obsolescence_audit(stdscr):

    client = EOLClient()
    last_results = []
    current = 0

    while True:

        stdscr.attrset(0)
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

        footer = "↑ ↓ naviguer | ENTER sélectionner | Q retour"
        stdscr.attrset(curses.color_pair(1))
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0:
            current -= 1

        elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
            current += 1

        elif key in (10, 13):

            # =====================================================
            # 1. LISTER VERSIONS OS
            # =====================================================
            if current == 0:

                stdscr.clear()

                label = "Produit endoflife (ex: ubuntu, windows-server): "
                stdscr.addstr(5, 4, label)

                curses.echo()
                product = stdscr.getstr(5, 4 + len(label), 50).decode().strip()
                curses.noecho()

                try:
                    releases = client.list_releases(product)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Versions pour {product} :")
                    stdscr.addstr(5, 4, "VERSION        EOL DATE        STATUT")

                    line = 7

                    for r in releases:
                        cycle = r.get("name") or r.get("cycle") or "N/A"
                        eol = extract_eol_date(r)
                        status = get_status(eol)

                        text = f"{cycle:<15} {eol:<15} {status}"

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))

                stdscr.getch()

            # =====================================================
            # 2. LISTE PAR RESEAU (CIDR)
            # =====================================================
            elif current == 1:

                stdscr.clear()

                label = "Réseau CIDR (ex: 192.168.1.0/24) : "
                stdscr.addstr(5, 4, label)

                curses.echo()
                network = stdscr.getstr(5, 4 + len(label), 30).decode().strip()
                curses.noecho()

                try:
                    assets = fetch_assets_from_db()
                    filtered = get_assets_in_network(network, assets)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Machines dans {network} :")

                    stdscr.addstr(5, 4, "HOSTNAME        IP              OS              VERSION")

                    line = 7

                    for a in filtered:
                        text = f"{a.hostname:<15} {a.ip:<15} {a.os_name:<20} {a.os_version}"

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    if not filtered:
                        stdscr.addstr(7, 4, "Aucun équipement trouvé.")

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))

                stdscr.getch()

            # =====================================================
            # 3. AUDIT BDD
            # =====================================================
            elif current == 2:

                stdscr.clear()
                stdscr.addstr(5, 4, "Audit depuis la base...")
                stdscr.refresh()

                try:
                    assets = fetch_assets_from_db()
                    last_results = audit_assets(assets, client)

                    json_path = write_report_json(last_results)
                    csv_path = write_report_csv(last_results)

                    stdscr.addstr(7, 4, "Audit terminé")
                    stdscr.addstr(8, 4, f"JSON : {json_path}")
                    stdscr.addstr(9, 4, f"CSV  : {csv_path}")

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))

                stdscr.getch()

            # =====================================================
            # 4. AUDIT CSV
            # =====================================================
            elif current == 3:

                stdscr.clear()
                stdscr.addstr(5, 4, "Chemin CSV : ")

                curses.echo()
                path = stdscr.getstr(5, 20, 200).decode()
                curses.noecho()

                try:
                    assets = read_assets_from_csv(path)
                    last_results = audit_assets(assets, client)

                    json_path = write_report_json(last_results)
                    csv_path = write_report_csv(last_results)

                    stdscr.addstr(7, 4, "Audit terminé")
                    stdscr.addstr(8, 4, f"JSON : {json_path}")
                    stdscr.addstr(9, 4, f"CSV  : {csv_path}")

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))

                stdscr.getch()

            # =====================================================
            # 5. EXPORT
            # =====================================================
            elif current == 4:

                stdscr.clear()

                if not last_results:
                    stdscr.addstr(5, 4, "Aucun audit disponible")
                else:
                    csv_path = write_report_csv(last_results)
                    stdscr.addstr(5, 4, f"Export CSV : {csv_path}")

                stdscr.getch()

            # =====================================================
            # 6. RETOUR
            # =====================================================
            elif current == 5:
                return

        elif key in (ord("q"), ord("Q")):
            return