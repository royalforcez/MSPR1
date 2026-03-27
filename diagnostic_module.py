import curses
import time
import json
import os
import logging
from datetime import datetime
from decimal import Decimal

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

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def screen_diagnostic(stdscr):
    global cached_data, cached_services, last_db_update, db_status
    
    logging.info("Entrée dans le module Diagnostic.")
    
    # Configuration curses locale
    stdscr.nodelay(True)
    curses.curs_set(1)
    
    search_text = ""
    active_tab = 0 
    selected_row = 0 
    db_online = False 
    
    tabs = [" [F1] GÉNÉRAL ", " [F2] ÉTAT SERVICES "]
    export_msg = ""
    export_msg_time = 0

    try:
        while True:
            current_time = time.time()
            stdscr.erase()
            h, w = stdscr.getmaxyx()

            # --- 1. LOGIQUE DE MISE À JOUR ---
            if not cached_data or (current_time - last_db_update > REFRESH_INTERVAL):
                last_db_update = current_time
                try:
                    result = get_db_data()
                    db_status = check_db_health() 
                    
                    if isinstance(result, list):
                        cached_data = result
                        cached_services = get_services_data() 
                        db_online = db_status["ntl"][0]
                        if not db_online:
                            logging.warning(f"Base NTL hors-ligne : {db_status['ntl'][1]}")
                    else:
                        db_online = False
                except Exception as e:
                    logging.error(f"Erreur de rafraîchissement des données : {e}")
                    db_online = False

            # --- 2. VUE : DESSIN ---
            draw_header(stdscr, tabs, active_tab, w)
            filtered = [d for d in cached_data if search_text.lower() in d.get('Nom', '').lower()]

            if active_tab == 0:
                if db_online:
                    if selected_row >= len(filtered) > 0:
                        selected_row = len(filtered) - 1
                    draw_diagnostic_table(stdscr, filtered, search_text, selected_row, h, w)
                else:
                    msg_err = " !!! CONNEXION BASE NTL PERDUE !!! "
                    try:
                        stdscr.addstr(h//2, (w-len(msg_err))//2, msg_err, curses.color_pair(4) | curses.A_BOLD)
                    except: pass
            elif active_tab == 1:
                draw_services_interface(stdscr, h, w, db_status, cached_services)

            # --- 3. BARRE D'ÉTAT ---
            timer_val = max(0, int(REFRESH_INTERVAL - (current_time - last_db_update)))
            try:
                stdscr.addstr(0, w - 12, f"Sync: {timer_val}s", curses.A_DIM)
            except: pass
            
            if export_msg and (current_time - export_msg_time < 3):
                try:
                    stdscr.addstr(h - 2, w - len(export_msg) - 2, export_msg, curses.color_pair(2) | curses.A_BOLD)
                except: pass

            footer = " F1/F2: Onglets | F3: Export JSON | ↑↓: Naviguer | ESC: Home "
            try:
                stdscr.addstr(h - 1, 1, footer.ljust(w-2), curses.A_REVERSE)
            except: pass
            
            stdscr.refresh()

            # --- 4. GESTION CLAVIER ---
            try:
                key = stdscr.getch()
            except:
                key = -1

            # Touches communes (Navigation / Quitter)
            if key == 27: # ESC
                logging.info("Sortie du module Diagnostic vers Home.")
                stdscr.nodelay(False)
                return 0 

            elif key == curses.KEY_F1:
                active_tab = 0
                selected_row = 0
                logging.info("Changement d'onglet : F1")

            elif key == curses.KEY_F2:
                active_tab = 1
                logging.info("Changement d'onglet : F2")

            elif key == curses.KEY_F3:
                try:
                    if not os.path.exists(EXPORT_DIR): 
                        os.makedirs(EXPORT_DIR)
                    
                    ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{EXPORT_DIR}/diag_{'gen' if active_tab==0 else 'serv'}_{ts_file}.json"
                    
                    data_to_save = filtered if (active_tab == 0 and search_text.strip()) else cached_data
                    export_data = {
                        "timestamp": datetime.now().isoformat(),
                        "module": "Diagnostic",
                        "data": data_to_save if active_tab == 0 else cached_services
                    }

                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=4, cls=DecimalEncoder)
                    
                    logging.info(f"Export réussi : {filename}")
                    export_msg = f" ✅ EXPORT : {os.path.basename(filename)} "
                    export_msg_time = time.time()
                except Exception as e:
                    logging.error(f"Échec de l'export JSON : {e}")
                    export_msg = " ❌ ERREUR EXPORT "
                    export_msg_time = time.time()

            elif key == curses.KEY_UP:
                selected_row = max(0, selected_row - 1)
            elif key == curses.KEY_DOWN:
                selected_row += 1

            # Touches spécifiques à l'onglet Général (Recherche)
            elif active_tab == 0:
                if key in (curses.KEY_BACKSPACE, 127, 8):
                    search_text = search_text[:-1]
                    selected_row = 0
                elif 32 <= key <= 126:
                    search_text += chr(key)
                    selected_row = 0

            time.sleep(0.05)

    except Exception as e:
        logging.error(f"Erreur fatale dans le module Diagnostic : {e}", exc_info=True)
        return 1