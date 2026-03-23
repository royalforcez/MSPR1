import curses
import ipaddress
from datetime import datetime

from .eol_api import EOLClient
from .audit_db import fetch_assets_from_db
from .audit_csv import read_assets_from_csv
from .audit_engine import audit_assets
from .reports import write_report_csv


MODULES = [
    "Lister les versions d’un OS et leurs dates de fin de vie",
    "Lister les composants d’une plage réseau",
    "Lancer un audit depuis la base de données",
    "Lancer un audit depuis un fichier CSV",
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
# FILTRAGE RESEAU
# =====================================================

def get_assets_in_network(network_cidr, assets):

    network = ipaddress.ip_network(network_cidr, strict=False)

    return [
        a for a in assets
        if a.ip and ipaddress.ip_address(a.ip) in network
    ]


# =====================================================
# INTERFACE PRINCIPALE
# =====================================================

def screen_obsolescence_audit(stdscr):

    stdscr.keypad(True)

    client = EOLClient()
    current = 0

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
            # 1. VERSIONS OS
            # =====================================================
            if current == 0:

                stdscr.clear()

                label = "Produit (ex: ubuntu, debian, windows-server): "
                stdscr.addstr(5, 4, label)

                curses.echo()
                stdscr.move(5, 4 + len(label))
                stdscr.clrtoeol()
                product = stdscr.getstr().decode("utf-8").strip()
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

                footer = "ESC: retour"
                stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                stdscr.refresh()

                while True:
                    k = stdscr.getch()
                    if k == 27:
                        break

            # =====================================================
            # 2. LISTE RESEAU
            # =====================================================
            elif current == 1:

                stdscr.clear()

                label = "Réseau CIDR (ex: 192.168.1.0/24) : "
                stdscr.addstr(5, 4, label)

                curses.echo()
                stdscr.move(5, 4 + len(label))
                stdscr.clrtoeol()
                network = stdscr.getstr().decode("utf-8").strip()
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

                    footer = "F3: Export CSV | ESC: retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3 and filtered:

                            class TempResult:
                                def __init__(self, a):
                                    self.hostname = a.hostname
                                    self.ip = a.ip
                                    self.os_name = a.os_name
                                    self.os_version = a.os_version
                                    self.status = ""
                                    self.eol_date = ""

                            export_data = [TempResult(a) for a in filtered]

                            path = write_report_csv(export_data, source="network")

                            msg = f"Export : {path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))
                    stdscr.getch()

            # =====================================================
            # 3. AUDIT BDD
            # =====================================================
            elif current == 2:

                stdscr.clear()
                stdscr.addstr(5, 4, "Audit en cours...")
                stdscr.refresh()

                try:
                    assets = fetch_assets_from_db()
                    results = audit_assets(assets, client)

                    stdscr.clear()
                    stdscr.addstr(5, 4, "Audit terminé ✔")

                    footer = "F3: Export CSV | ESC: Retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3:
                            path = write_report_csv(results, source="db")

                            msg = f"Export : {path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

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
                stdscr.move(5, 20)
                stdscr.clrtoeol()
                path = stdscr.getstr().decode("utf-8").strip()
                curses.noecho()

                try:
                    assets = read_assets_from_csv(path)
                    results = audit_assets(assets, client)

                    stdscr.clear()
                    stdscr.addstr(5, 4, "Audit terminé ✔")

                    footer = "F3: Export CSV | ESC: Retour"
                    stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

                    stdscr.refresh()

                    while True:
                        k = stdscr.getch()

                        if k == curses.KEY_F3:
                            export_path = write_report_csv(results, source="csv")

                            msg = f"Export : {export_path}"
                            msg_y = h - 3

                            stdscr.move(msg_y, 0)
                            stdscr.clrtoeol()
                            stdscr.addstr(msg_y, (w - len(msg)) // 2, msg)
                            stdscr.refresh()

                        elif k == 27:
                            break

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))
                    stdscr.getch()

            # RETOUR
            elif current == 4:
                return

        elif key == 27:
            return