import curses
from ui import draw_frame
from diagnostic_module import screen_diagnostic
from wms_backup import screen_wms_backup
from obsolescence import screen_obsolescence_audit

MODULES = [
    "1. Module Diagnostic",
    "2. Module Sauvegarde WMS",
    "3. Module Audit d’Obsolescence",
    "Q. Quitter"
]

APP_NAME = [

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

def draw_frame(stdscr, top):
    h, w = stdscr.getmaxyx()
    bottom = h - 2

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


def screen_home(stdscr):
    current = 0

    while True:
        # --- RÉINITIALISATION TOTALE ---
        stdscr.attrset(0)  # Éteint tous les attributs (couleurs/gras)
        stdscr.clear()     # Efface l'écran complètement
        
        # On redéfinit les paires ici pour écraser les changements des modules
        curses.init_pair(1, curses.COLOR_WHITE, -1)  # Blanc (Normal)
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Vert (Sélection)
        curses.init_pair(3, curses.COLOR_CYAN, -1)   # Cyan (Titre)

        h, w = stdscr.getmaxyx()

        # Titre (Cyan)
        x_title = (w - max(len(l) for l in APP_NAME)) // 2
        stdscr.attron(curses.color_pair(3))
        for i, line in enumerate(APP_NAME):
            if i < h: # Sécurité
                stdscr.addstr(i, x_title, line)
        stdscr.attroff(curses.color_pair(3))

        frame_top = len(APP_NAME) + 1
        draw_frame(stdscr, frame_top)

        # Menu
        for i, module in enumerate(MODULES):
            # On définit la couleur : Vert si courant, sinon Blanc
            cp = curses.color_pair(2 if i == current else 1)
            
            # On applique la couleur et on force le texte normal pour les non-sélectionnés
            stdscr.attrset(cp) 
            if i == current:
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(frame_top + 2 + i, 4, f"> {module}")
                stdscr.attroff(curses.A_BOLD)
            else:
                stdscr.addstr(frame_top + 2 + i, 4, f"  {module}")

        # Footer
        stdscr.attrset(curses.color_pair(1))
        footer = "↑ ↓ naviguer | ENTER sélectionner | Q quitter"
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
            current += 1
        elif key in (10, 13):
            if current == 0:
                screen_diagnostic(stdscr)
            elif current == 1:
                screen_wms_backup(stdscr)
            elif current == 2:
                screen_obsolescence_audit(stdscr)
            elif current == 3:
                break
        elif key in (ord("q"), ord("Q")):
            break
        