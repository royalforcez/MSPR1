import curses
import ipaddress
from datetime import datetime

from session_manager import get_db_connection_ntl
from obsolescence.eol_api import EOLClient


MODULES = [
    "Lister les versions d’un OS et leurs dates de fin de vie",
    "Lister les composants d’une plage réseau",
    "Lancer un audit depuis la base de données",
    "Retour au menu principal"
]


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

        elif key in (10, 13):

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
                    client = EOLClient()
                    releases = client.list_releases(product)

                    stdscr.clear()
                    stdscr.addstr(3, 4, f"Versions pour {product} :")
                    stdscr.addstr(5, 4, "VERSION        EOL DATE        STATUT")

                    line = 7

                    for r in releases:

                        version = r.get("cycle") or r.get("name") or "N/A"
                        eol = r.get("eol") or "N/A"

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
            # 2. RESEAU (BDD)
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

                    for r in filtered:
                        hostname, ip, os_name, version, _ = r

                        text = f"{hostname:<15} {ip:<15} {os_name:<20} {version}"

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    stdscr.addstr(h - 1, 2, "ESC: retour")

                    while stdscr.getch() != 27:
                        pass

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur BDD : {e}")
                    stdscr.getch()

            # =====================================================
            # 3. AUDIT BDD
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

                    for r in rows:

                        hostname, ip, os_name, version, eol = r

                        status = get_status(eol)
                        eol_str = str(eol) if eol else "N/A"

                        text = f"{hostname:<15} {ip:<15} {os_name:<20} {version:<10} {eol_str:<12} {status}"

                        if line < h - 2:
                            stdscr.addstr(line, 4, text)
                            line += 1

                    stdscr.addstr(h - 1, 2, "ESC: retour")

                    while stdscr.getch() != 27:
                        pass

                except Exception as e:
                    stdscr.addstr(7, 4, f"Erreur BDD : {e}")
                    stdscr.getch()

            # =====================================================
            # RETOUR
            # =====================================================
            elif current == 3:
                return

        elif key == 27:
            return