import curses

def draw_services_interface(stdscr, h, w, db_status, services_data):
    """Dessine l'interface F2 dynamique par serveur."""
    is_alive, msg = db_status
    
    # --- PARTIE HAUTE : BDD ---
    stdscr.addstr(3, 2, "╔" + "═"*(w-6) + "╗")
    stdscr.addstr(4, 2, "║  STATUS BASE DE DONNÉES" + " "*(w-30) + "║", curses.A_BOLD)
    
    color = curses.color_pair(2) if is_alive else curses.color_pair(4)
    status_symbol = "● ONLINE" if is_alive else "○ OFFLINE"
    
    stdscr.addstr(5, 4, f"Etat : {status_symbol}", color | curses.A_BOLD)
    stdscr.addstr(6, 4, f"Info : {msg[:w-10]}")
    stdscr.addstr(7, 2, "╚" + "═"*(w-6) + "╝")

    # --- PARTIE BASSE : DIAGNOSTIC AD/DNS ---
    mid_y = 10
    stdscr.addstr(mid_y, 2, "╔" + "═"*(w-6) + "╗")
    stdscr.addstr(mid_y + 1, 2, "║  DIAGNOSTIC SERVICES (AD / DNS)" + " "*(w-38) + "║", curses.A_BOLD)
    
    y_offset = mid_y + 3

    if not services_data:
        stdscr.addstr(y_offset, 5, "EN ATTENTE DES DONNÉES...", curses.A_DIM)
        y_offset += 2
    else:
        for server, services in services_data.items():
            if y_offset >= h - 4: 
                break
            stdscr.addstr(y_offset, 5, f"Serveur : {server}", curses.A_UNDERLINE | curses.A_BOLD)
            y_offset += 1

            ad_status = services.get("Active Directory", "INCONNU")
            dns_status = services.get("DNS", "INCONNU")

            ad_color = curses.color_pair(2) | curses.A_BOLD if ad_status == "UP" else (curses.color_pair(4) | curses.A_BOLD if ad_status == "DOWN" else curses.A_DIM)
            dns_color = curses.color_pair(2) | curses.A_BOLD if dns_status == "UP" else (curses.color_pair(4) | curses.A_BOLD if dns_status == "DOWN" else curses.A_DIM)

            stdscr.addstr(y_offset, 5, "  [!] Service Active Directory : ", curses.A_BOLD)
            stdscr.addstr(y_offset, 38, ad_status, ad_color)
            y_offset += 1
            
            stdscr.addstr(y_offset, 5, "  [!] Résolution DNS (Local)   : ", curses.A_BOLD)
            stdscr.addstr(y_offset, 38, dns_status, dns_color)
            y_offset += 2

    stdscr.addstr(y_offset, 2, "╚" + "═"*(w-6) + "╝")