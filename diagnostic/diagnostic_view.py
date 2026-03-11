import curses

def draw_header(stdscr, tabs, active_tab, w):
    """Dessine les onglets en haut."""
    stdscr.addstr(1, 0, " " * w) 
    for i, tab_name in enumerate(tabs):
        style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
        stdscr.addstr(1, 2 + (i * 22), tab_name, style)

def draw_diagnostic_table(stdscr, data, search_text, selected_row, h, w):
    """Dessine uniquement le tableau de l'onglet Général adapté à la nouvelle BDD."""
    # 1. Barre de recherche
    stdscr.attrset(0)
    stdscr.addstr(3, 2, "RECHERCHE : ", curses.A_BOLD)
    stdscr.addstr(3, 15, search_text + "_", curses.color_pair(2))

    # 2. Configuration des colonnes (Ajustées pour la lisibilité)
    col_nom, col_ip = int(w * 0.15), int(w * 0.14)
    col_os, col_ver = int(w * 0.10), int(w * 0.10)
    col_cpu, col_ram = int(w * 0.08), int(w * 0.08)
    col_up, col_site = int(w * 0.14), int(w * 0.12)

    def fmt(text, size, last=False):
        t = str(text) if text is not None and text != "" else "N/A"
        content = t[:size-2].ljust(size-1)
        return content if last else f"{content}|"

    # 3. En-tête (MAJ des noms)
    header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
              f"{fmt('VER.', col_ver)}{fmt('CPU %', col_cpu)}"
              f"{fmt('RAM %', col_ram)}{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
    
    stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
    try:
        stdscr.addstr(5, 1, header[:w-2])
    except curses.error: pass
    stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

    # 4. Données
    y_offset = 6
    for i, srv in enumerate(data):
        if y_offset < h - 2:
            # Récupération des nouvelles clés de la BDD
            cpu_val = srv.get('CPU_Percent') or 0
            ram_val = srv.get('RAM_Usage_Percent') or 0
            
            # Formatage de la ligne avec les nouvelles clés
            line_str = (f"{fmt(srv.get('Nom'), col_nom)}"
                        f"{fmt(srv.get('IPv4'), col_ip)}"
                        f"{fmt(srv.get('OS'), col_os)}"
                        f"{fmt(srv.get('Version'), col_ver)}"
                        f"{fmt(str(cpu_val)+'%', col_cpu)}"
                        f"{fmt(str(ram_val)+'%', col_ram)}" # Changé de 'G' à '%'
                        f"{fmt(srv.get('uptime'), col_up)}"
                        f"{fmt(srv.get('Site'), col_site, True)}")

            # Style : Rouge (color_pair 4) si CPU > 80% ou RAM > 90%
            if i == selected_row:
                style = curses.color_pair(2) | curses.A_REVERSE
            elif cpu_val > 80 or ram_val > 90:
                style = curses.color_pair(4) | curses.A_BOLD
            else:
                style = 0

            try:
                stdscr.addstr(y_offset, 1, line_str[:w-2], style)
            except curses.error: pass
            y_offset += 1