import curses

def draw_header(stdscr, tabs, active_tab, w):
    """Dessine les onglets en haut."""
    stdscr.addstr(1, 0, " " * w) 
    for i, tab_name in enumerate(tabs):
        style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
        stdscr.addstr(1, 2 + (i * 22), tab_name, style)

def draw_diagnostic_table(stdscr, data, search_text, selected_row, h, w):
    """Dessine le tableau de diagnostic avec l'OS de la table Equipements."""
    
    # 1. Barre de recherche
    stdscr.attrset(0)
    stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
    stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

    # 2. Configuration des colonnes (Ajustées : suppression VER, gain de place OS/NOM)
    col_nom = int(w * 0.18)
    col_ip  = int(w * 0.14)
    col_os  = int(w * 0.16)  # Augmenté pour bien voir Windows/Linux
    col_cpu = int(w * 0.08)
    col_ram = int(w * 0.08)
    col_up  = int(w * 0.16)
    col_site = int(w * 0.14)

    def fmt(text, size, last=False):
        t = str(text) if text is not None and text != "" else "N/A"
        # On tronque si c'est trop long pour la colonne
        content = t[:size-2].ljust(size-1)
        return content if last else f"{content}|"

    # 3. En-tête (MAJ : Suppression de Version)
    header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
              f"{fmt('CPU %', col_cpu)}{fmt('RAM %', col_ram)}"
              f"{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
    
    stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
    try:
        stdscr.addstr(5, 1, header[:w-2])
    except curses.error: pass
    stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

    # 4. Affichage des données
    y_offset = 6
    for i, srv in enumerate(data):
        if y_offset < h - 2:
            # Récupération des valeurs numériques pour le style
            cpu_val = srv.get('CPU_Percent') or 0
            ram_val = srv.get('RAM_Usage_Percent') or 0
            
            # Formatage de la ligne (On utilise srv.get('OS') qui vient de Equipements)
            line_str = (f"{fmt(srv.get('Nom'), col_nom)}"
                        f"{fmt(srv.get('IPv4'), col_ip)}"
                        f"{fmt(srv.get('OS'), col_os)}"
                        f"{fmt(str(cpu_val)+'%', col_cpu)}"
                        f"{fmt(str(ram_val)+'%', col_ram)}"
                        f"{fmt(srv.get('uptime'), col_up)}"
                        f"{fmt(srv.get('Site'), col_site, True)}")

            # Détermination du style de la ligne
            if i == selected_row:
                style = curses.color_pair(2) | curses.A_REVERSE
            elif cpu_val > 80 or ram_val > 90:
                style = curses.color_pair(4) | curses.A_BOLD  # Alerte ressources
            else:
                style = 0

            try:
                stdscr.addstr(y_offset, 1, line_str[:w-2], style)
            except curses.error: pass
            y_offset += 1