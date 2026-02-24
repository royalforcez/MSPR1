import curses
import mysql.connector

def check_db_health():
    """Vérifie la santé de la BDD avec un timeout très court pour ne pas figer le CLI."""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1", 
            user="root", 
            password="", 
            database="ntlsystools",
            connect_timeout=1  # <--- IMPORTANT : N'attend que 1 seconde max
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return True, "Connecté au serveur MySQL (127.0.0.1:3306)"
    except Exception:
        return False, "Impossible de joindre le serveur SQL (Timeout ou Service éteint)"

def draw_services_interface(stdscr, h, w):
    """Dessine l'interface F2."""
    # PARTIE HAUTE : BDD
    stdscr.addstr(3, 2, "╔" + "═"*(w-6) + "╗")
    stdscr.addstr(4, 2, "║  STATUS BASE DE DONNÉES" + " "*(w-30) + "║", curses.A_BOLD)
    
    is_alive, msg = check_db_health()
    color = curses.color_pair(2) if is_alive else curses.color_pair(4)
    status_symbol = "● ONLINE" if is_alive else "○ OFFLINE"
    
    stdscr.addstr(5, 4, f"Etat : {status_symbol}", color | curses.A_BOLD)
    stdscr.addstr(6, 4, f"Info : {msg[:w-10]}")
    stdscr.addstr(7, 2, "╚" + "═"*(w-6) + "╝")

    # PARTIE BASSE : DIAGNOSTIC
    mid_y = 10
    stdscr.addstr(mid_y, 2, "╔" + "═"*(w-6) + "╗")
    stdscr.addstr(mid_y + 1, 2, "║  DIAGNOSTIC SERVICES (AD / DNS)" + " "*(w-38) + "║", curses.A_BOLD)
    stdscr.addstr(mid_y + 3, 5, "[!] En attente de configuration...", curses.A_DIM)
    stdscr.addstr(mid_y + 5, 2, "╚" + "═"*(w-6) + "╝")