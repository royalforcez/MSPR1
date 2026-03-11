import curses

def draw_services_interface(stdscr, h, w, db_status):
    """Dessine l'interface F2 (Services & AD/DNS)."""
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
    
    # Simulation de tests futurs
    stdscr.addstr(mid_y + 3, 5, "[!] Service Active Directory : ", curses.A_BOLD)
    stdscr.addstr(mid_y + 3, 35, "EN ATTENTE", curses.A_DIM)
    
    stdscr.addstr(mid_y + 4, 5, "[!] Résolution DNS (Local)   : ", curses.A_BOLD)
    stdscr.addstr(mid_y + 4, 35, "EN ATTENTE", curses.A_DIM)
    
    stdscr.addstr(mid_y + 6, 2, "╚" + "═"*(w-6) + "╝")