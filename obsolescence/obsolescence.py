import curses
import ipaddress
import time
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


def display_audit_results(stdscr, results, source):
    """
    Sous-écran dédié à l'affichage des résultats + export F3
    """

    export_msg = ""
    export_time = 0

    while True:

        stdscr.clear()
        h, w = stdscr.getmaxyx()

        stdscr.addstr(2, 4, f"Résultats audit ({source})")
        stdscr.addstr(4, 4, "HOSTNAME        IP              OS              VERSION        STATUS")

        line = 6

        for r in results:
            text = f"{r.hostname:<15} {r.ip:<15} {r.os_name:<15} {r.os_version:<10} {r.status}"
            if line < h - 4:
                stdscr.addstr(line, 4, text)
                line += 1

        # Footer avec F3 uniquement ici
        footer = "F3: Export CSV | ESC: Retour"
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        # Message export
        if export_msg and (time.time() - export_time < 3):
            stdscr.addstr(h - 2, w - len(export_msg) - 2, export_msg, curses.A_BOLD)

        stdscr.refresh()
        key = stdscr.getch()

        # EXPORT
        if key == curses.KEY_F3:
            try:
                path = write_report_csv(results, source)
                export_msg = f"Export : {path.split('/')[-1]}"
            except Exception as e:
                export_msg = f"Erreur: {str(e)[:20]}"

            export_time = time.time()

        elif key == 27:  # ESC
            return


def get_assets_in_network(network_cidr, assets):

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


def screen_obsolescence_audit(stdscr):

    client = EOLClient()
    current = 0

    while True:

        stdscr.clear()
        h, w = stdscr.getmaxyx()

        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

        title = "Module Audit d’Obsolescence"

        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3))

        for i, module in enumerate(MODULES):

            cp = curses.color_pair(2 if i == current else 1)

            stdscr.attrset(cp)

            if i == current:
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(6 + i, 4, f"> {module}")
                stdscr.attroff(curses.A_BOLD)
            else:
                stdscr.addstr(6 + i, 4, f"  {module}")

        # Footer SANS F3 ici
        footer = "↑ ↓ naviguer | ENTER sélectionner | Q retour"
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0:
            current -= 1

        elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
            current += 1

        elif key in (10, 13):

            # =========================
            # AUDIT DB
            # =========================
            if current == 2:

                stdscr.clear()
                stdscr.addstr(5, 4, "Audit depuis la base...")
                stdscr.refresh()

                try:
                    assets = fetch_assets_from_db()
                    results = audit_assets(assets, client)

                    display_audit_results(stdscr, results, "db")

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))
                    stdscr.getch()

            # =========================
            # AUDIT CSV
            # =========================
            elif current == 3:

                stdscr.clear()
                stdscr.addstr(5, 4, "Chemin CSV : ")

                curses.echo()
                path = stdscr.getstr(5, 20, 200).decode()
                curses.noecho()

                try:
                    assets = read_assets_from_csv(path)
                    results = audit_assets(assets, client)

                    display_audit_results(stdscr, results, "csv")

                except Exception as e:
                    stdscr.addstr(7, 4, str(e))
                    stdscr.getch()

            elif current == 4:
                return

        elif key in (ord("q"), ord("Q")):
            return