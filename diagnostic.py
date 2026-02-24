import curses
import mysql.connector
import time
from services import draw_services_interface

# --- VARIABLES DE CACHE ---
cached_data = []
last_db_update = 0
REFRESH_INTERVAL = 5  # Rafraîchissement BDD toutes les 5 secondes

def get_db_data():
    """Récupère les données de la BDD avec un timeout strict et les jointures nécessaires."""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="ntlsystools",
            connect_timeout=1 # Sécurité contre les freezes réseau
        )
        cursor = conn.cursor(dictionary=True)
        
        # Requête optimisée
        query = """
        SELECT 
            e.Nom, e.IPv4, eol.OS, eol.Version, 
            r.CPU, r.RAM, r.uptime, s.Nom as Site
        FROM Equipements e
        LEFT JOIN EndOfLife eol ON e.ID_EOL = eol.ID
        LEFT JOIN UtilisationRessources r ON e.ID = r.ID_Equipement
        LEFT JOIN Sites s ON e.ID_Site = s.ID
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return str(e)

def screen_diagnostic(stdscr):
    global cached_data, last_db_update
    
    stdscr.nodelay(True)  # Mode non-bloquant pour le temps réel
    curses.curs_set(1) 
    
    search_text = ""
    active_tab = 0 
    selected_row = 0 
    tabs = [" [F1] GÉNÉRAL ", " [F2] ÉTAT SERVICES ", " [F3] SERVICES "]

    while True:
        current_time = time.time()
        stdscr.erase() # Évite les clignotements
        h, w = stdscr.getmaxyx()
        filtered_data = [] 

        # --- 1. LOGIQUE DE CACHE ---
        if not cached_data or (current_time - last_db_update > REFRESH_INTERVAL):
            new_data = get_db_data()
            if isinstance(new_data, list):
                cached_data = new_data
                last_db_update = current_time

        # --- 2. DESSIN DU HEADER ---
        stdscr.addstr(1, 0, " " * w) 
        for i, tab_name in enumerate(tabs):
            style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
            stdscr.addstr(1, 2 + (i * 22), tab_name, style)

        # --- 3. LOGIQUE D'AFFICHAGE ---
        if active_tab == 0:
            stdscr.attrset(0)
            stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
            stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

            # Calcul des largeurs responsives
            col_nom, col_ip = int(w * 0.15), int(w * 0.14)
            col_os, col_ver = int(w * 0.10), int(w * 0.12)
            col_cpu, col_ram = int(w * 0.07), int(w * 0.07)
            col_up, col_site = int(w * 0.15), int(w * 0.12)

            def fmt(text, size, last=False):
                t = str(text) if text is not None else "N/A"
                content = t[:size-2].ljust(size-1)
                return content if last else f"{content}|"

            header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
                      f"{fmt('VERSION', col_ver)}{fmt('CPU', col_cpu)}"
                      f"{fmt('RAM', col_ram)}{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
            
            stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
            stdscr.addstr(5, 1, header[:w-2])
            stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

            # Filtrage
            filtered_data = [d for d in cached_data if search_text.lower() in d['Nom'].lower()]
            
            if selected_row >= len(filtered_data):
                selected_row = max(0, len(filtered_data) - 1)

            y_offset = 6
            for i, srv in enumerate(filtered_data):
                if y_offset < h - 2:
                    # --- SÉCURISATION DES DONNÉES (Fix TypeError) ---
                    cpu_val = srv.get('CPU') if srv.get('CPU') is not None else 0
                    ram_val = srv.get('RAM') if srv.get('RAM') is not None else 0
                    
                    line_str = (f"{fmt(srv['Nom'], col_nom)}{fmt(srv['IPv4'], col_ip)}{fmt(srv['OS'], col_os)}"
                                f"{fmt(srv['Version'], col_ver)}{fmt(str(cpu_val)+'%', col_cpu)}"
                                f"{fmt(str(ram_val)+'G', col_ram)}{fmt(srv['uptime'], col_up)}"
                                f"{fmt(srv['Site'], col_site, True)}")

                    if i == selected_row:
                        style = curses.color_pair(2) | curses.A_REVERSE
                    else:
                        style = curses.color_pair(4) if cpu_val > 80 else 0

                    stdscr.addstr(y_offset, 1, line_str[:w-2], style)
                    y_offset += 1

        elif active_tab == 1:
            draw_services_interface(stdscr, h, w)

        # --- 4. FOOTER ET SYNC ---
        timer = int(REFRESH_INTERVAL - (current_time - last_db_update))
        stdscr.addstr(0, w-20, f"Sync: {max(0, timer)}s", curses.A_DIM)
        stdscr.attrset(0)
        stdscr.addstr(h - 1, 1, " F1/F2/F3: Onglets | ↑↓: Naviguer | ESC: Home ", curses.A_REVERSE)
        
        stdscr.refresh()

        # --- 5. GESTION CLAVIER ---
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == 27: break
        elif key == curses.KEY_F1: active_tab = 0
        elif key == curses.KEY_F2: active_tab = 1
        elif key == curses.KEY_F3: active_tab = 2
        elif key == curses.KEY_UP:
            selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN:
            if filtered_data:
                selected_row = min(len(filtered_data) - 1, selected_row + 1)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            search_text = search_text[:-1]
            selected_row = 0
        elif 32 <= key <= 126:
            search_text += chr(key)
            selected_row = 0

        time.sleep(0.05)