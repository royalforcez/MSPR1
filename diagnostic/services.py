import curses

def draw_services_interface(stdscr, h, w, db_status, services_data):
    """Dessine l'interface F2 sans aucun bug de trait ou de bordure."""
    
    ntl_alive, ntl_msg = db_status["ntl"]
    ent_alive, ent_msg = db_status["entreprise"]

    box_width = w - 8

    def draw_box_line(y, content, style=0):
        """Dessine une ligne avec un début et une fin de cadre fixes."""
        stdscr.addstr(y, 2, "║")
        inner_w = box_width - 2
        text = content[:inner_w].ljust(inner_w)
        stdscr.addstr(y, 3, text, style)
        stdscr.addstr(y, 3 + inner_w, "║")

    # --- CADRE HAUT : STATUS BASES ---

    stdscr.addstr(3, 2, "╔" + "═" * (box_width - 2) + "╗")
    
    draw_box_line(4, "   SITUATION DES BASES DE DONNÉES", curses.A_BOLD)
    
    color_ntl = curses.color_pair(2) if ntl_alive else curses.color_pair(4)
    stdscr.addstr(5, 2, "║")
    stdscr.addstr(5, 4, " BDD NTL        : ", curses.A_BOLD)
    stdscr.addstr(5, 22, "● ONLINE" if ntl_alive else "○ OFFLINE", color_ntl | curses.A_BOLD)
    remplissage = " " * (box_width - 32 - len(ntl_msg[:20]))
    stdscr.addstr(5, 32, f"[{ntl_msg[:20]}]" + remplissage)
    stdscr.addstr(5, 2 + box_width - 1, "║")

    color_ent = curses.color_pair(2) if ent_alive else curses.color_pair(4)
    stdscr.addstr(6, 2, "║")
    stdscr.addstr(6, 4, " BDD ENTREPRISE : ", curses.A_BOLD)
    stdscr.addstr(6, 22, "● ONLINE" if ent_alive else "○ OFFLINE", color_ent | curses.A_BOLD)
    remplissage_ent = " " * (box_width - 32 - len(ent_msg[:20]))
    stdscr.addstr(6, 32, f"[{ent_msg[:20]}]" + remplissage_ent)
    stdscr.addstr(6, 2 + box_width - 1, "║")
    
    stdscr.addstr(7, 2, "╚" + "═" * (box_width - 2) + "╝")

    # --- CADRE BAS : SERVICES AD/DNS ---
    mid_y = 9
    stdscr.addstr(mid_y, 2, "╔" + "═" * (box_width - 2) + "╗")
    draw_box_line(mid_y + 1, "   DIAGNOSTIC SERVICES (AD / DNS)", curses.A_BOLD)
    draw_box_line(mid_y + 2, "")
    
    y_offset = mid_y + 3

    if not services_data:
        draw_box_line(y_offset, "      EN ATTENTE DES DONNÉES...")
        y_offset += 1
    else:
        for server, services in services_data.items():
            if y_offset >= h - 7: break 
            
            draw_box_line(y_offset, f"     Serveur : {server}", curses.A_UNDERLINE | curses.A_BOLD)
            y_offset += 1

            # Services
            for s_name in ["Active Directory", "DNS"]:
                s_status = services.get(s_name, "N/A")
                s_color = curses.color_pair(2) if s_status == "UP" else curses.color_pair(4)
                
                stdscr.addstr(y_offset, 2, "║")
                stdscr.addstr(y_offset, 8, f"[!] {s_name.ljust(25)} : ")
                stdscr.addstr(y_offset, 38, s_status, s_color | curses.A_BOLD)
                stdscr.addstr(y_offset, 38 + len(s_status), " " * (box_width - 37 - len(s_status)))
                stdscr.addstr(y_offset, 2 + box_width - 1, "║")
                y_offset += 1
            
            draw_box_line(y_offset, "")
            y_offset += 1


    stdscr.addstr(y_offset, 2, "╚" + "═" * (box_width - 2) + "╝")


