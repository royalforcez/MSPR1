import curses

# Stockage en RAM des deux environnements
DB_NTL = {
    "host": "", "user": "", "password": "", "database": "ntlsystools"
}

DB_ENTREPRISE = {
    "host": "", "user": "", "password": "", "database": "prod_wms"
}

NAS_CONFIG = {
    "ip": "192.168.1.11", "user": "", "password": "", "share": "NAS-Lille"
}

def ask_credentials(stdscr):
    curses.echo()
    h, w = stdscr.getmaxyx()
    
    def input_win(y, label, current_val=""):
        stdscr.addstr(y, 4, label)
        # On affiche la valeur par défaut si elle existe
        res = stdscr.getstr(y, 4 + len(label), 30).decode('utf-8')
        return res if res else current_val

    stdscr.clear()
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(1, (w-40)//2, "🔐 CONFIGURATION DES ACCÈS RÉSEAU")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    # --- SECTION BDD NTL ---
    stdscr.addstr(3, 2, "[ 1. BASE DE DONNÉES NTL (TP) ]", curses.A_REVERSE)
    DB_NTL["host"] = input_win(5, "IP Serveur : ")
    DB_NTL["user"] = input_win(6, "Utilisateur : ")
    stdscr.addstr(7, 4, "Mot de passe : ")
    curses.noecho()
    DB_NTL["password"] = stdscr.getstr(7, 4 + 15, 30).decode('utf-8')
    curses.echo()

    # --- SECTION BDD ENTREPRISE ---
    stdscr.addstr(9, 2, "[ 2. BASE DE DONNÉES ENTREPRISE ]", curses.A_REVERSE)
    DB_ENTREPRISE["host"] = input_win(11, "IP Serveur : ")
    DB_ENTREPRISE["user"] = input_win(12, "Utilisateur : ")
    stdscr.addstr(13, 4, "Mot de passe : ")
    curses.noecho()
    DB_ENTREPRISE["password"] = stdscr.getstr(13, 4 + 15, 30).decode('utf-8')
    curses.echo()

    # --- SECTION NAS ---
    stdscr.addstr(15, 2, "[ 3. NAS DE LILLE ]", curses.A_REVERSE)
    NAS_CONFIG["user"] = input_win(17, "Utilisateur NAS : ")
    stdscr.addstr(18, 4, "Mot de passe NAS : ")
    curses.noecho()
    NAS_CONFIG["password"] = stdscr.getstr(18, 4 + 17, 30).decode('utf-8')
    
    curses.noecho()
    curses.curs_set(0)