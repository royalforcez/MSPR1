import curses
import mysql.connector
import time
from services import draw_services_interface

# --- VARIABLES DE CACHE ---
cached_data = []
last_db_update = 0
REFRESH_INTERVAL = 5  # On ne rafraîchit les données que toutes les 5 secondes


def get_db_data():
<<<<<<< Updated upstream
    """Récupère les données avec un timeout strict."""
=======
    """Récupère les données de la base de données avec les jointures nécessaires."""
>>>>>>> Stashed changes
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
<<<<<<< Updated upstream
            database="ntlsystools",
            connect_timeout=1
        )
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT 
            e.Nom, e.IPv4, eol.OS, eol.Version, 
            r.CPU, r.RAM, r.uptime, s.Nom as Site
        FROM Equipements e
        LEFT JOIN EndOfLife eol ON e.ID_EOL = eol.ID
        LEFT JOIN UtilisationRessources r ON e.ID = r.ID_Equipement
        LEFT JOIN Sites s ON e.ID_Site = s.ID
=======
            database="ntlsystools"
        )
        cursor = conn.cursor(dictionary=True)
        
        # Requête SQL optimisée avec JOIN pour séparer OS et Version
        query = """
        SELECT 
            e.Nom, 
            e.IPv4, 
            eol.OS, 
            eol.Version, 
            r.CPU, 
            r.RAM, 
            r.uptime, 
            s.Nom as Site
        FROM Equipements e
        LEFT JOIN EndOfLife eol ON e.ID_EOL = eol.ID
        LEFT JOIN UtilisationRessources r ON e.ID = r.ID_Equipement
        LEFT JOIN Sites s ON e.ID = s.ID_Site
>>>>>>> Stashed changes
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
<<<<<<< Updated upstream
=======
        # On retourne l'erreur sous forme de chaîne de caractères pour l'afficher
>>>>>>> Stashed changes
        return str(e)

def screen_diagnostic(stdscr):
    global cached_data, last_db_update
    
    stdscr.nodelay(True)  # Ne bloque pas le programme
    curses.curs_set(1) 
    
    search_text = ""
    active_tab = 0 
    selected_row = 0 
    tabs = [" [F1] GÉNÉRAL ", " [F2] ÉTAT SERVICES ", " [F3] SERVICES "]

    while True:
        current_time = time.time()
        stdscr.erase() # Plus fluide que clear() (évite le clignotement)
        h, w = stdscr.getmaxyx()
        
        # --- INITIALISATION DE SÉCURITÉ ---
        # On s'assure que filtered_data existe même si la BDD est vide ou en erreur
        filtered_data = [] 

<<<<<<< Updated upstream
        # --- 1. LOGIQUE DE CACHE (DÉCOUPLAGE BDD / AFFICHAGE) ---
        # On ne va voir la BDD que si le cache est vide ou expiré
        if not cached_data or (current_time - last_db_update > REFRESH_INTERVAL):
            new_data = get_db_data()
            if isinstance(new_data, list):
                cached_data = new_data
                last_db_update = current_time
            else:
                # Si erreur, on garde les vieilles données mais on affiche l'erreur
                pass

        # --- 2. DESSIN DU HEADER (ONGLETS) ---
=======
        # --- 1. BOUTONS (ONGLETS) ---
>>>>>>> Stashed changes
        stdscr.addstr(1, 0, " " * w) 
        for i, tab_name in enumerate(tabs):
            style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
            stdscr.addstr(1, 2 + (i * 22), tab_name, style)

<<<<<<< Updated upstream
        # --- 3. LOGIQUE D'AFFICHAGE ---
        if active_tab == 0:
            # Recherche
            stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
            stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

            # Colonnes
            col_nom, col_ip = int(w * 0.15), int(w * 0.14)
            col_os, col_ver = int(w * 0.10), int(w * 0.12)
            col_cpu, col_ram, col_up, col_site = int(w*0.07), int(w*0.07), int(w*0.15), int(w*0.12)

            def fmt(text, size, last=False):
                t = str(text) if text else "N/A"
                c = t[:size-2].ljust(size-1)
                return c if last else f"{c}|"

            header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
                      f"{fmt('VERSION', col_ver)}{fmt('CPU', col_cpu)}{fmt('RAM', col_ram)}"
                      f"{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
            
            stdscr.addstr(5, 1, header[:w-2], curses.A_UNDERLINE | curses.color_pair(3))
=======
        # --- 2. BARRE DE RECHERCHE ---
        stdscr.attrset(0)
        stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
        stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

        # --- 3. CALCUL DES LARGEURS RESPONSIVES ---
        col_nom     = int(w * 0.15)
        col_ip      = int(w * 0.14)
        col_os      = int(w * 0.10)
        col_version = int(w * 0.12)
        col_cpu     = int(w * 0.07)
        col_ram     = int(w * 0.07)
        col_up      = int(w * 0.15)
        col_site    = int(w * 0.12)

        def fmt(text, size, last=False):
            t = str(text) if text else "N/A"
            content = t[:size-2].ljust(size-1)
            return content if last else f"{content}|"

        # --- 4. EN-TÊTE DU TABLEAU ---
        header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
                  f"{fmt('VERSION', col_version)}{fmt('CPU', col_cpu)}"
                  f"{fmt('RAM', col_ram)}{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
        
        stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
        stdscr.addstr(5, 1, header[:w-2])
        stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

        # --- 5. RÉCUPÉRATION ET AFFICHAGE DES DONNÉES ---
        data = get_db_data() 
        
        if isinstance(data, list):
            y_offset = 6
            # Filtrage selon la barre de recherche
            filtered_data = [d for d in data if search_text.lower() in d['Nom'].lower()]
            
            # Ajustement de la sélection si la liste change après un filtre
            if selected_row >= len(filtered_data):
                selected_row = max(0, len(filtered_data) - 1)
>>>>>>> Stashed changes

            # Utilisation des données en CACHE (super rapide)
            filtered_data = [d for d in cached_data if search_text.lower() in d['Nom'].lower()]
            
            y_offset = 6
            for i, srv in enumerate(filtered_data):
                if y_offset < h - 2:
<<<<<<< Updated upstream
                    line = (f"{fmt(srv['Nom'], col_nom)}{fmt(srv['IPv4'], col_ip)}{fmt(srv['OS'], col_os)}"
                            f"{fmt(srv['Version'], col_ver)}{fmt(str(srv['CPU'])+'%', col_cpu)}"
                            f"{fmt(str(srv['RAM'])+'G', col_ram)}{fmt(srv['uptime'], col_up)}"
                            f"{fmt(srv['Site'], col_site, True)}")
                    
                    style = curses.color_pair(2) | curses.A_REVERSE if i == selected_row else 0
                    stdscr.addstr(y_offset, 1, line[:w-2], style)
                    y_offset += 1

        elif active_tab == 1:
            draw_services_interface(stdscr, h, w)

        # --- 4. INDICATEUR DE CHARGEMENT DISCRET ---
        # Affiche dans combien de temps les données seront rafraîchies
        timer = int(REFRESH_INTERVAL - (current_time - last_db_update))
        stdscr.addstr(0, w-20, f"Sync: {max(0, timer)}s", curses.A_DIM)

        stdscr.addstr(h - 1, 1, " F1/F2/F3: Onglets | ↑↓: Naviguer | ESC: Home ", curses.A_REVERSE)
        stdscr.refresh()

        # --- 5. GESTION DES TOUCHES (Maintenant instantanée) ---
        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == 27: break
        elif key == curses.KEY_F1: active_tab = 0
        elif key == curses.KEY_F2: active_tab = 1
        elif key == curses.KEY_F3: active_tab = 2
        elif key == curses.KEY_UP: selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN:
            if 'filtered_data' in locals() and filtered_data:
=======
                    line_str = (f"{fmt(srv['Nom'], col_nom)}"
                                f"{fmt(srv['IPv4'], col_ip)}"
                                f"{fmt(srv['OS'], col_os)}"
                                f"{fmt(srv['Version'], col_version)}"
                                f"{fmt(str(srv['CPU'])+'%', col_cpu)}"
                                f"{fmt(str(srv['RAM'])+'G', col_ram)}"
                                f"{fmt(srv['uptime'], col_up)}"
                                f"{fmt(srv['Site'], col_site, True)}")

                    # Style de la ligne (sélection ou alerte)
                    if i == selected_row:
                        style = curses.color_pair(2) | curses.A_REVERSE
                    else:
                        style = curses.color_pair(4) if srv.get('CPU', 0) > 80 else 0

                    stdscr.addstr(y_offset, 1, line_str[:w-2], style)
                    y_offset += 1
        else:
            # Si data est une string, c'est un message d'erreur de connexion
            stdscr.addstr(6, 2, f"Erreur de connexion BDD : {data}", curses.color_pair(4))
        
        # --- 6. FOOTER ---
        stdscr.attrset(0)
        stdscr.addstr(h - 1, 1, " F1/F2/F3: Onglets | ↑↓: Naviguer | ESC: Home ", curses.A_REVERSE)
        stdscr.refresh()

        # --- 7. GESTION DES ENTRÉES CLAVIER ---
        key = stdscr.getch()

        if key == 27: # Touche ESC pour quitter
            break
        elif key == curses.KEY_F1: active_tab = 0
        elif key == curses.KEY_F2: active_tab = 1
        elif key == curses.KEY_F3: active_tab = 2
        elif key == curses.KEY_UP:
            selected_row = max(0, selected_row - 1)
        elif key == curses.KEY_DOWN:
            # On vérifie que filtered_data n'est pas vide avant de descendre
            if filtered_data:
>>>>>>> Stashed changes
                selected_row = min(len(filtered_data) - 1, selected_row + 1)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            search_text = search_text[:-1]
            selected_row = 0
        elif 32 <= key <= 126:
            search_text += chr(key)
            selected_row = 0
<<<<<<< Updated upstream

        time.sleep(0.05) # 20 FPS pour l'interface, stable et fluide
=======
>>>>>>> Stashed changes
