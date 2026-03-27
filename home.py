import curses
import logging
from ui import draw_frame
from diagnostic_module import screen_diagnostic
from wms_backup import screen_wms_backup
from obsolescence_screen import screen_obsolescence_audit

MODULES = [
    "1. Module Diagnostic",
    "2. Module Sauvegarde WMS/NTL",
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

def screen_home(stdscr):
    """Menu principal. Retourne 0 à la fermeture."""
    current = 0
    logging.info("Affichage du menu principal.")

    while True:
        try:
            # --- RÉINITIALISATION ---
            stdscr.attrset(0)
            stdscr.clear()
            
            # Réassignation des couleurs par sécurité
            curses.init_pair(1, curses.COLOR_WHITE, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_CYAN, -1)

            h, w = stdscr.getmaxyx()

            # Titre (Cyan)
            x_title = (w - max(len(l) for l in APP_NAME)) // 2
            stdscr.attron(curses.color_pair(3))
            for i, line in enumerate(APP_NAME):
                if i < h: 
                    stdscr.addstr(i, x_title, line)
            stdscr.attroff(curses.color_pair(3))

            frame_top = len(APP_NAME) + 1
            draw_frame(stdscr, frame_top)

            # Menu
            for i, module in enumerate(MODULES):
                cp = curses.color_pair(2 if i == current else 1)
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
            if h > 1:
                stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

            stdscr.refresh()
            key = stdscr.getch()

            # Navigation
            if key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
                current += 1
            
            # Sélection
            elif key in (10, 13):
                status = 0
                if current == 0:
                    logging.info("Lancement Module Diagnostic")
                    status = screen_diagnostic(stdscr)
                elif current == 1:
                    logging.info("Lancement Module Sauvegarde")
                    status = screen_wms_backup(stdscr)
                elif current == 2:
                    logging.info("Lancement Module Audit")
                    status = screen_obsolescence_audit(stdscr)
                elif current == 3: # Quitter
                    break
                
                # Log du retour du module
                if status != 0:
                    logging.error(f"Le module {current + 1} a retourné une erreur (Code {status})")
                else:
                    logging.info(f"Retour au menu principal depuis module {current + 1}")

            elif key in (ord("q"), ord("Q")):
                break

        except Exception as e:
            logging.error(f"Erreur dans le menu principal : {e}")
            return 1 # Code erreur pour le main

    logging.info("Fermeture du menu principal.")
    return 0
        