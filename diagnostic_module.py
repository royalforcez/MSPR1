import curses
import time
from diagnostic.data_manager import get_db_data, check_db_health, get_services_data
from diagnostic.diagnostic_view import draw_header, draw_diagnostic_table
from diagnostic.services import draw_services_interface

# --- VARIABLES DE CACHE ---
cached_data = []
cached_services = {}
last_db_update = 0
REFRESH_INTERVAL = 5
db_status = (False, "Initialisation...") # Stocke (is_alive, message)

def screen_diagnostic(stdscr):
    global cached_data, cached_services, last_db_update, db_status
    stdscr.nodelay(True)
    curses.curs_set(1)
    
    search_text = ""
    active_tab = 0 
    selected_row = 0 
    db_online = False 
    tabs = [" [F1] GÉNÉRAL ", " [F2] ÉTAT SERVICES "]

    while True:
        current_time = time.time()
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # --- 1. LOGIQUE DE MISE À JOUR (Toutes les 5s) ---
        if not cached_data or (current_time - last_db_update > REFRESH_INTERVAL):
            result = get_db_data()
            db_status = check_db_health() 
            
            if isinstance(result, list):
                cached_data = result
                cached_services = get_services_data() 
                db_online = True
                last_db_update = current_time
            else:
                db_online = False 

        # --- 2. VUE : DESSIN DE L'INTERFACE ---
        draw_header(stdscr, tabs, active_tab, w)

        if active_tab == 0:
            if db_online:
                filtered = [d for d in cached_data if search_text.lower() in d['Nom'].lower()]
                
                if selected_row >= len(filtered) and len(filtered) > 0:
                    selected_row = len(filtered) - 1
                
                draw_diagnostic_table(stdscr, filtered, search_text, selected_row, h, w)
            else:
                if isinstance(result, str) and "Erreur SQL" in result:
                    stdscr.addstr(h//2, 2, " !!! ERREUR DANS LA REQUÊTE SQL !!! ", curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(h//2 + 1, 2, result[:w-4], curses.A_DIM)
                else:
                    msg = " !!! CONNEXION BASE DE DONNÉES PERDUE !!! "
                    retry_in = int(REFRESH_INTERVAL - (current_time - last_db_update))
                    retry_msg = f"Tentative de reconnexion automatique dans {max(0, retry_in)}s..."
                    stdscr.addstr(h//2, (w-len(msg))//2, msg, curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(h//2 + 1, (w-len(retry_msg))//2, retry_msg, curses.A_DIM)

        elif active_tab == 1:
            draw_services_interface(stdscr, h, w, db_status, cached_services)

        # --- 3. BARRE D'ÉTAT ET SYNC ---
        timer = int(REFRESH_INTERVAL - (current_time - last_db_update))
        sync_txt = f"Sync: {max(0, timer)}s"
        stdscr.addstr(0, w - len(sync_txt) - 2, sync_txt, curses.A_DIM)
        stdscr.addstr(h - 1, 1, " F1/F2: Onglets | ↑↓: Naviguer | ESC: Home ", curses.A_REVERSE)
        
        stdscr.refresh()

        # --- 4. GESTION DES ENTRÉES CLAVIER ---
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == 27: # ESC
            stdscr.nodelay(False)
            break
        elif key == curses.KEY_F1: 
            active_tab = 0
            selected_row = 0
        elif key == curses.KEY_F2: 
            active_tab = 1
        elif key == curses.KEY_UP: 
            selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN: 
            selected_row += 1
        elif key in (curses.KEY_BACKSPACE, 127, 8): 
            search_text = search_text[:-1]
            selected_row = 0
        elif 32 <= key <= 126:
            search_text += chr(key)
            selected_row = 0

        time.sleep(0.05)