import curses

# --- STOCKAGE RAM (VIDE AU DÉMARRAGE) ---
DB_NTL = {
    "host": "", "user": "", "password": "", "database": "ntlsystools"
}

DB_ENTREPRISE = {
    "host": "", "user": "", "password": "", "database": "ntlsystools"
}

NAS_CONFIG = {
    "ip": "", "user": "", "password": "", "share": ""
}

def ask_credentials(stdscr):
    """Demande l'intégralité des accès au démarrage."""
    
    # Initialisation des couleurs
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    
    h, w = stdscr.getmaxyx()
    curses.echo() 
    curses.curs_set(1) 

    def input_field(y, label):
        """Saisie obligatoire (aucune valeur par défaut)."""
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, 4, label)
        # On récupère la saisie et on nettoie les espaces
        return stdscr.getstr(y, 4 + len(label), 40).decode('utf-8').strip()

    stdscr.clear()

    # --- TITRE ---
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(1, (w - 38) // 2, "🔐 CONFIGURATION DES ACCÈS RÉSEAU")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    # --- SECTION 1 : BDD NTL ---
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(3, 2, "[ 1. BASE DE DONNÉES NTL (TP) ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(3))
    
    DB_NTL["host"] = input_field(5, "IP Serveur   : ")
    DB_NTL["user"] = input_field(6, "Utilisateur  : ")
    
    stdscr.addstr(7, 4, "Mot de passe : ")
    curses.noecho()
    DB_NTL["password"] = stdscr.getstr(7, 4 + 15, 40).decode('utf-8').strip()
    curses.echo()

    # --- SECTION 2 : BDD ENTREPRISE ---
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(9, 2, "[ 2. BASE DE DONNÉES ENTREPRISE ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(3))
    
    DB_ENTREPRISE["host"] = input_field(11, "IP Serveur   : ")
    DB_ENTREPRISE["user"] = input_field(12, "Utilisateur  : ")
    
    stdscr.addstr(13, 4, "Mot de passe : ")
    curses.noecho()
    DB_ENTREPRISE["password"] = stdscr.getstr(13, 4 + 15, 40).decode('utf-8').strip()
    curses.echo()

    # --- SECTION 3 : NAS LILLE ---
    stdscr.attron(curses.color_pair(2))
    stdscr.addstr(15, 2, "[ 3. CONFIGURATION NAS LILLE ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(2))
    
    NAS_CONFIG["ip"]    = input_field(17, "IP du NAS     : ")
    NAS_CONFIG["share"] = input_field(18, "Nom du Partage: ")
    NAS_CONFIG["user"]  = input_field(19, "Utilisateur   : ")
    
    stdscr.addstr(20, 4, "Mot de passe  : ")
    curses.noecho()
    NAS_CONFIG["password"] = stdscr.getstr(20, 4 + 16, 40).decode('utf-8').strip()

    # --- FINALISATION ---
    curses.noecho()
    curses.curs_set(0)
    stdscr.clear()
    stdscr.addstr(h // 2, (w - 20) // 2, "✅ Configuration OK", curses.color_pair(2))
    stdscr.refresh()
    curses.napms(1000)