import curses
import time
import json
import os
from datetime import datetime

from diagnostic.data_manager import get_db_data, check_db_health, get_services_data
from diagnostic.diagnostic_view import draw_header, draw_diagnostic_table
from diagnostic.services import draw_services_interface

# --- CONFIGURATION ---
REFRESH_INTERVAL = 5
EXPORT_DIR = "exports"

# --- VARIABLES DE CACHE ---
cached_data = []
cached_services = {}
last_db_update = 0
db_status = {"ntl": (False, "Init..."), "entreprise": (False, "Init...")}

def screen_diagnostic(stdscr):
    global cached_data, cached_services, last_db_update, db_status
    
    stdscr.nodelay(True)
    curses.curs_set(1)
    
    search_text = ""
    active_tab = 0 
    selected_row = 0 
    db_online = False 
    # Ajout de F3 dans la liste des onglets/fonctions en haut si tu veux, 
    # mais on va surtout le mettre dans le footer.
    tabs = [" [F1] GÉNÉRAL ", " [F2] ÉTAT SERVICES "]
    
    export_msg = ""
    export_msg_time = 0

    while True:
        current_time = time.time()
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # --- 1. LOGIQUE DE MISE À JOUR ---
        if not cached_data or (current_time - last_db_update > REFRESH_INTERVAL):
            last_db_update = current_time
            result = get_db_data()
            db_status = check_db_health() 
            
            if isinstance(result, list):
                cached_data = result
                cached_services = get_services_data() 
                db_online = db_status["ntl"][0]
            else:
                db_online = False 

        # --- 2. VUE : DESSIN ---
        draw_header(stdscr, tabs, active_tab, w)
        filtered = [d for d in cached_data if search_text.lower() in d['Nom'].lower()]

        if active_tab == 0:
            if db_online:
                if selected_row >= len(filtered) > 0:
                    selected_row = len(filtered) - 1
                draw_diagnostic_table(stdscr, filtered, search_text, selected_row, h, w)
            else:
                msg_err = " !!! CONNEXION BASE NTL PERDUE !!! "
                stdscr.addstr(h//2, (w-len(msg_err))//2, msg_err, curses.color_pair(4) | curses.A_BOLD)

        elif active_tab == 1:
            draw_services_interface(stdscr, h, w, db_status, cached_services)

        # --- 3. BARRE D'ÉTAT ET NOTIFICATIONS ---
        timer_val = max(0, int(REFRESH_INTERVAL - (current_time - last_db_update)))
        stdscr.addstr(0, w - 12, f"Sync: {timer_val}s", curses.A_DIM)
        
        if export_msg and (current_time - export_msg_time < 3):
            stdscr.addstr(h - 2, w - len(export_msg) - 2, export_msg, curses.color_pair(2) | curses.A_BOLD)

        # FOOTER MAJ AVEC F3
        footer = " F1/F2: Onglets | F3: Export JSON | ↑↓: Naviguer | ESC: Home "
        stdscr.addstr(h - 1, 1, footer.ljust(w-2), curses.A_REVERSE)
        
        stdscr.refresh()

        # --- 4. GESTION CLAVIER ---
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == 27: # ESC
            stdscr.nodelay(False)
            break
        elif key == curses.KEY_F1: 
            active_tab, selected_row = 0, 0
        elif key == curses.KEY_F2: 
            active_tab = 1
        
        # --- LOGIQUE TOUCHE F3 (EXPORT) ---
        elif key == curses.KEY_F3:
            try:
                if not os.path.exists(EXPORT_DIR): os.makedirs(EXPORT_DIR)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if active_tab == 0:
                    filename = f"{EXPORT_DIR}/export_general_{timestamp}.json"
                    export_data = {
                        "view": "Général",
                        "filter": search_text,
                        "data": filtered
                    }
                else:
                    filename = f"{EXPORT_DIR}/export_services_{timestamp}.json"
                    export_data = {
                        "view": "Services",
                        "db_status": db_status,
                        "data": cached_services
                    }

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                
                export_msg = f" Fichier créé : {os.path.basename(filename)} "
                export_msg_time = time.time()
            except Exception as e:
                export_msg = f" Erreur: {str(e)[:20]} "
                export_msg_time = time.time()

        elif key == curses.KEY_UP: 
            selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN: 
            selected_row += 1

        # Recherche (Uniquement sur l'onglet général)
        elif active_tab == 0:
            if key in (curses.KEY_BACKSPACE, 127, 8): 
                search_text = search_text[:-1]
                selected_row = 0
            elif 32 <= key <= 126:
                search_text += chr(key)
                selected_row = 0

        time.sleep(0.05)