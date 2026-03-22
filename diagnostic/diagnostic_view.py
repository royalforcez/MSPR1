import curses

def draw_header(stdscr, tabs, active_tab, w):
    """Dessine les onglets en haut de l'écran."""
    stdscr.addstr(1, 0, " " * w) 
    for i, tab_name in enumerate(tabs):
        style = curses.A_REVERSE | curses.A_BOLD if i == active_tab else curses.color_pair(3)
        try:
            stdscr.addstr(1, 2 + (i * 22), tab_name, style)
        except curses.error: pass

def draw_diagnostic_table(stdscr, data, search_text, selected_row, h, w):
    """Dessine le tableau de diagnostic (Onglet F1)."""
    
    # 1. Barre de recherche
    stdscr.attrset(0)
    stdscr.addstr(3, 2, " RECHERCHE : ", curses.A_BOLD)
    stdscr.addstr(3, 15, f"{search_text}_", curses.color_pair(2) | curses.A_BOLD)

    # 2. Configuration dynamique des colonnes
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
        content = t[:size-2].ljust(size-1)
        return content if last else f"{content}|"

    # 3. En-tête du tableau
    header = (f"{fmt('NOM', col_nom)}{fmt('IP', col_ip)}{fmt('OS', col_os)}"
              f"{fmt('CPU', col_cpu)}{fmt('RAM', col_ram)}{fmt('DSK', col_dsk)}"
              f"{fmt('UPTIME', col_up)}{fmt('SITE', col_site, True)}")
    
    stdscr.attron(curses.A_UNDERLINE | curses.color_pair(3))
    try:
        stdscr.addstr(5, 1, header[:w-2])
    except curses.error: pass
    stdscr.attroff(curses.A_UNDERLINE | curses.color_pair(3))

    # 4. Affichage des lignes de données
    y_offset = 6
    for i, srv in enumerate(data):
        if y_offset < h - 3: # On laisse une ligne de plus pour l'info JSON
            cpu_val = srv.get('CPU_Percent') or 0
            ram_val = srv.get('RAM_Usage_Percent') or 0
            dsk_val = srv.get('disk_usage_percent') or 0 
            
            line_str = (f"{fmt(srv.get('Nom'), col_nom)}"
                        f"{fmt(srv.get('IPv4'), col_ip)}"
                        f"{fmt(srv.get('OS'), col_os)}"
                        f"{fmt(f'{int(cpu_val)}%', col_cpu)}"
                        f"{fmt(f'{int(ram_val)}%', col_ram)}"
                        f"{fmt(f'{int(dsk_val)}%', col_dsk)}" 
                        f"{fmt(srv.get('uptime'), col_up)}"
                        f"{fmt(srv.get('Site'), col_site, True)}")

            if i == selected_row:
                style = curses.color_pair(2) | curses.A_REVERSE
            elif cpu_val > 80 or ram_val > 90 or dsk_val > 90:
                style = curses.color_pair(4) | curses.A_BOLD  
            else:
                style = 0

            try:
                stdscr.addstr(y_offset, 1, line_str[:w-2], style)
            except curses.error: pass
            y_offset += 1