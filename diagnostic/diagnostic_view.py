import curses
import logging

def draw_header(stdscr, tabs, active_tab, w):
    """Dessine les onglets en haut de l'écran."""
    try:
        # Nettoyage de la ligne d'en-tête
        stdscr.addstr(1, 0, " " * (w - 1)) 
        for i, tab_name in enumerate(tabs):
            # Style : Inversé si actif, Cyan sinon
            style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
            # Positionnement dynamique
            pos_x = 2 + (i * 22)
            if pos_x + len(tab_name) < w:
                stdscr.addstr(1, pos_x, tab_name, style)
    except curses.error:
        # On ne logue pas l'erreur ici pour éviter de spammer le log à chaque refresh
        pass

def draw_diagnostic_table(stdscr, data, search_text, selected_row, h, w):
    """Dessine le tableau de diagnostic (Onglet F1)."""
    
    try:
        # 1. Barre de recherche (Lisibilité renforcée)
        stdscr.attrset(0)
        stdscr.addstr(3, 2, " RECHERCHE : ", curses.A_BOLD)
        # Affichage du texte de recherche en vert
        stdscr.addstr(3, 15, f"{search_text}", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(3, 15 + len(search_text), "_", curses.A_BLINK) # Curseur clignotant

        # 2. Configuration dynamique des colonnes (Ratios)
        # On s'assure que les colonnes s'adaptent à la largeur de la fenêtre
        col_nom  = int(w * 0.16)
        col_ip   = int(w * 0.13)
        col_os   = int(w * 0.14)
        col_cpu  = int(w * 0.07)
        col_ram  = int(w * 0.07)
        col_dsk  = int(w * 0.07) 
        col_up   = int(w * 0.14)
        col_site = int(w * 0.12)

        def fmt(text, size, last=False):
            t = str(text) if text is not None and text != "" else "N/A"
            # On tronque si c'est trop long, on complète si c'est trop court
            content = t[:size-2].ljust(size-1)
            return content if last else f"{content}|"

        # 3. En-tête du tableau
        header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
                  f"{fmt('CPU', col_cpu)}{fmt('RAM', col_ram)}{fmt('DSK', col_dsk)}"
                  f"{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
        
        stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
        stdscr.addstr(5, 1, header[:w-2])
        stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

        # 4. Affichage des lignes de données
        y_offset = 6
        for i, srv in enumerate(data):
            if y_offset < h - 3:
                # Extraction et conversion sécurisée des valeurs numériques
                try:
                    cpu_val = float(srv.get('CPU_Percent') or 0)
                    ram_val = float(srv.get('RAM_Usage_Percent') or 0)
                    dsk_val = float(srv.get('disk_usage_percent') or 0)
                except (ValueError, TypeError):
                    cpu_val, ram_val, dsk_val = 0, 0, 0
                
                # Construction de la ligne
                line_str = (f"{fmt(srv.get('Nom'), col_nom)}"
                            f"{fmt(srv.get('IPv4'), col_ip)}"
                            f"{fmt(srv.get('OS'), col_os)}"
                            f"{fmt(f'{int(cpu_val)}%', col_cpu)}"
                            f"{fmt(f'{int(ram_val)}%', col_ram)}"
                            f"{fmt(f'{int(dsk_val)}%', col_dsk)}" 
                            f"{fmt(srv.get('uptime'), col_up)}"
                            f"{fmt(srv.get('Site'), col_site, True)}")

                # --- LOGIQUE DE COULEUR (Codes exploitables visuellement) ---
                if i == selected_row:
                    style = curses.color_pair(2) | curses.A_REVERSE # Sélectionné (Vert inversé)
                elif cpu_val > 85 or ram_val > 90 or dsk_val > 90:
                    style = curses.color_pair(4) | curses.A_BOLD    # ALERTE (Rouge/Gras)
                elif cpu_val > 70 or ram_val > 80:
                    style = curses.color_pair(3)                    # WARNING (Cyan)
                else:
                    style = curses.color_pair(1)                    # NORMAL (Blanc)

                stdscr.addstr(y_offset, 1, line_str[:w-2], style)
                y_offset += 1

    except Exception as e:
        # En cas de crash d'affichage, on logue pour débugger les problèmes de taille d'écran
        logging.error(f"Erreur d'affichage du tableau diagnostic : {e}")