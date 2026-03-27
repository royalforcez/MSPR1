import curses
import time
import logging

def init_colors():
    """Initialise les couleurs. Retourne 0 si OK, 1 sinon."""
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)   # normal
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # selected
        curses.init_pair(3, curses.COLOR_CYAN, -1)    # title
        return 0
    except Exception as e:
        logging.error(f"Erreur initialisation couleurs: {e}")
        return 1

def loading_screen(stdscr):
    """Affiche l'écran de chargement. Retourne 0 si fini, 1 si erreur."""
    try:
        logging.info("Affichage du loading_screen...")
        h, w = stdscr.getmaxyx()
        
        # Sécurité : Si le terminal est trop petit pour le logo
        if h < 15 or w < 60:
            logging.warning(f"Terminal trop petit ({w}x{h}). Saut de l'animation.")
            return 0 # On ne bloque pas l'appli pour ça, on continue

        bar_width = max(30, w - 50)
        logo = [
            "  ███╗   ██╗████████╗██╗        ███████╗██╗   ██╗███████╗",
            "  ████╗  ██║╚══██╔══╝██║        ██╔════╝╚██╗ ██╔╝██╔════╝",
            "  ██╔██╗ ██║   ██║   ██║        ███████╗ ╚████╔╝ ███████╗",
            "  ██║╚██╗██║   ██║   ██║        ╚════██║  ╚██╔╝  ╚════██║",
            "  ██║ ╚████║   ██║   ███████╗   ███████║   ██║   ███████║",
            "  ╚═╝  ╚═══╝   ╚═╝   ╚══════╝   ╚══════╝   ╚═╝   ╚══════╝ ",
            "████████╗ ██████╗  ██████╗ ██╗     ██████╗  ██████╗ ██╗  ██╗",
            "╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔══██╗██╔═══██╗╚██╗██╔╝",
            "   ██║   ██║   ██║██║   ██║██║     ██████╔╝██║   ██║ ╚███╔╝ ",
            "   ██║   ██║   ██║██║   ██║██║     ██╔══██╗██║   ██║ ██╔██╗ ",
            "   ██║   ╚██████╔╝╚██████╔╝███████╗██████╔╝╚██████╔╝██╔╝ ██╗",
            "   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═════╝  ╚═════╝ ╚═╝  ╚═╝"
        ]

        logo_width = max(len(line) for line in logo)
        logo_height = len(logo)
        start_y = max(2, (h // 2) - (logo_height // 2) - 3)
        logo_x = (w - logo_width) // 2

        for i in range(bar_width + 1):
            stdscr.clear()
            # Dessin du Logo
            stdscr.attron(curses.color_pair(3))
            for idx, line in enumerate(logo):
                stdscr.addstr(start_y + idx, logo_x, line)
            stdscr.attroff(curses.color_pair(3))

            # Texte d'état
            title = "Chargement des modules..."
            stdscr.addstr(start_y + logo_height + 1, (w - len(title)) // 2, title)

            # Barre de chargement
            bar = "█" * i + "░" * (bar_width - i)
            stdscr.attron(curses.color_pair(3))
            stdscr.addstr(start_y + logo_height + 3, (w - bar_width - 2) // 2, f"[{bar}]")
            stdscr.attroff(curses.color_pair(3))
            
            stdscr.refresh()
            time.sleep(0.012)
        
        logging.info("loading_screen terminé avec succès.")
        return 0

    except Exception as e:
        logging.error(f"Erreur durant l'écran de chargement: {e}")
        return 1

def draw_frame(stdscr, top):
    """Dessine un cadre. Retourne 0 si OK, 1 si erreur."""
    try:
        h, w = stdscr.getmaxyx()
        bottom = h - 2
        if bottom <= top + 2:
            return 0
            
        for x in range(1, w - 1):
            stdscr.addch(top, x, curses.ACS_HLINE)
            stdscr.addch(bottom, x, curses.ACS_HLINE)
        for y in range(top + 1, bottom):
            stdscr.addch(y, 0, curses.ACS_VLINE)
            stdscr.addch(y, w - 1, curses.ACS_VLINE)
            
        stdscr.addch(top, 0, curses.ACS_ULCORNER)
        stdscr.addch(top, w - 1, curses.ACS_URCORNER)
        stdscr.addch(bottom, 0, curses.ACS_LLCORNER)
        stdscr.addch(bottom, w - 1, curses.ACS_LRCORNER)
        return 0
    except Exception as e:
        logging.error(f"Erreur dessin cadre: {e}")
        return 1