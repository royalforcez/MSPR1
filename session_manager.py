import curses

# --- STOCKAGE RAM (COFFRE-FORT TEMPORAIRE) ---
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
    """Initialise les couleurs et demande les accès au démarrage."""
    
    # 1. Configuration des couleurs (pour éviter les soucis d'affichage)
    curses.start_color()
    curses.use_default_colors()
    # Paire 1 : Blanc sur Noir | Paire 2 : Vert | Paire 3 : Cyan (Ton bleu clair)
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)
    
    h, w = stdscr.getmaxyx()
    curses.echo() # Permet de voir ce qu'on tape (sauf mdp)
    curses.curs_set(1) # Affiche le curseur pour la saisie

    def input_field(y, label, current_val=""):
        """Aide à la saisie avec gestion de valeur par défaut."""
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, 4, label)
        # Saisie de l'utilisateur
        res = stdscr.getstr(y, 4 + len(label), 30).decode('utf-8').strip()
        return res if res else current_val

    stdscr.clear()

    # --- TITRE PRINCIPAL ---
    stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
    stdscr.addstr(1, (w - 38) // 2, "🔐 CONFIGURATION DES ACCÈS RÉSEAU")
    stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    # --- SECTION 1 : BDD NTL ---
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(3, 2, "[ 1. BASE DE DONNÉES NTL (TP) ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(3))
    
    DB_NTL["host"] = input_field(5, "IP Serveur   : ", "192.168.1.137")
    DB_NTL["user"] = input_field(6, "Utilisateur  : ", "admin_ntl")
    
    stdscr.addstr(7, 4, "Mot de passe : ")
    curses.noecho() # Cache le mot de passe
    DB_NTL["password"] = stdscr.getstr(7, 4 + 15, 30).decode('utf-8').strip()
    curses.echo()

    # --- SECTION 2 : BDD ENTREPRISE ---
    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(9, 2, "[ 2. BASE DE DONNÉES ENTREPRISE ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(3))
    
    DB_ENTREPRISE["host"] = input_field(11, "IP Serveur   : ", "127.0.0.1")
    DB_ENTREPRISE["user"] = input_field(12, "Utilisateur  : ", "root")
    
    stdscr.addstr(13, 4, "Mot de passe : ")
    curses.noecho()
    DB_ENTREPRISE["password"] = stdscr.getstr(13, 4 + 15, 30).decode('utf-8').strip()
    curses.echo()

    # --- SECTION 3 : NAS LILLE ---
    stdscr.attron(curses.color_pair(2)) # Vert pour le NAS
    stdscr.addstr(15, 2, "[ 3. CONFIGURATION NAS LILLE ]", curses.A_REVERSE)
    stdscr.attroff(curses.color_pair(2))
    
    NAS_CONFIG["user"] = input_field(17, "Utilisateur NAS : ", "admin_ntl")
    
    stdscr.addstr(18, 4, "Mot de passe NAS : ")
    curses.noecho()
    NAS_CONFIG["password"] = stdscr.getstr(18, 4 + 19, 30).decode('utf-8').strip()

    # --- FINALISATION ---
    curses.noecho()
    curses.curs_set(0) # Cache le curseur
    stdscr.clear()
    stdscr.addstr(h // 2, (w - 20) // 2, "✅ Configuration OK", curses.color_pair(2))
    stdscr.refresh()
    curses.napms(800) # Petite pause visuelle