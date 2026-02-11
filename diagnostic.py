import curses
import mysql.connector
from mysql.connector import Error

def get_db_data():
    """Récupère les données de diagnostic depuis le serveur SQL distant"""
    try:
        # --- CONFIGURATION À REMPLIR ---
        config = {
            'host': '127.0.0.1', # IP de ton serveur BDD
            'user': 'root',
            'password': '',
            'database': 'ntlsystools'
        }
        
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        
        # Requête pour récupérer OS, Ressources et Services concaténés
        query = """
        SELECT 
            e.Nom, e.OS, e.IPv4,
            eol.Version,
            r.CPU, r.RAM, r.Disk, r.uptime,
            GROUP_CONCAT(CONCAT(s.Nom_Services, ':', s.Etat)) as Services
        FROM Equipements e
        LEFT JOIN EndOfLife eol ON e.ID_EOL = eol.ID
        LEFT JOIN UtilisationRessources r ON e.ID = r.ID_Equipement
        LEFT JOIN EtatServices s ON e.ID = s.ID_Equipement
        GROUP BY e.ID;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return rows
    except Error as e:
        return f"Erreur de connexion : {e}"


def screen_diagnostic(stdscr):
    curses.curs_set(1) 
    search_text = ""
    active_tab = 0
    selected_row = 0 
    tabs = [" [F1] GÉNÉRAL ", " [F2] RÉSEAU ", " [F3] SERVICES "]
    
    while True:
        stdscr.attrset(0)
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # --- 1. BOUTONS ---
        stdscr.addstr(1, 0, " " * w) 
        for i, tab_name in enumerate(tabs):
            style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
            stdscr.addstr(1, 2 + (i * 20), tab_name, style)

        # --- 2. RECHERCHE ---
        stdscr.attrset(0)
        stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
        stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

        # --- 3. CALCUL LARGEURS (On réduit de 1 pour laisser place au "|") ---
        col_nom = int(w * 0.18)
        col_ip  = int(w * 0.14)
        col_os  = int(w * 0.14)
        col_cpu = int(w * 0.08)
        col_ram = int(w * 0.08)
        col_up  = int(w * 0.15)
        col_site = int(w * 0.12)

        # Fonction de formatage avec séparateur
        def fmt(text, size, last=False):
            text = str(text) if text else ""
            content = text[:size-2].ljust(size-1)
            return content if last else f"{content}|"

        # --- 4. EN-TÊTE ---
        header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
                  f"{fmt('CPU', col_cpu)}{fmt('RAM', col_ram)}{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
        
        stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
        stdscr.addstr(5, 1, header[:w-2])
        stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

        # --- 5. DONNÉES ---
        data = get_db_data() 
        
        if isinstance(data, list):
            y_offset = 6
            filtered_data = [d for d in data if search_text.lower() in d['Nom'].lower()]
            
            if selected_row >= len(filtered_data):
                selected_row = max(0, len(filtered_data) - 1)

            for i, srv in enumerate(filtered_data):
                if y_offset < h - 2:
                    line_str = (f"{fmt(srv['Nom'], col_nom)}"
                                f"{fmt(srv['IPv4'], col_ip)}"
                                f"{fmt(srv['OS'], col_os)}"
                                f"{fmt(str(srv['CPU'])+'%', col_cpu)}"
                                f"{fmt(str(srv['RAM'])+'G', col_ram)}"
                                f"{fmt(srv['uptime'], col_up)}"
                                f"{fmt(srv.get('Site', 'N/A'), col_site, True)}")

                    # Style de la ligne
                    if i == selected_row:
                        style = curses.color_pair(2) | curses.A_REVERSE
                    else:
                        style = curses.color_pair(4) if srv.get('CPU', 0) > 80 else 0

                    stdscr.addstr(y_offset, 1, line_str[:w-2], style)
                    y_offset += 1
        
        stdscr.attrset(0)
        stdscr.addstr(h - 1, 1, " F1/F2/F3: Onglets | ↑↓: Naviguer | ESC: Home ", curses.A_REVERSE)
        stdscr.refresh()

        # --- 6. TOUCHES ---
        key = stdscr.getch()
        if key == 27: break
        elif key == curses.KEY_F1: active_tab = 0
        elif key == curses.KEY_F2: active_tab = 1
        elif key == curses.KEY_F3: active_tab = 2
        elif key == curses.KEY_UP: selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN: selected_row = min(len(filtered_data) - 1, selected_row + 1)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            search_text = search_text[:-1]
            selected_row = 0
        elif 32 <= key <= 126:
            search_text += chr(key)
            selected_row = 0

