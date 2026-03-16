import curses
from home import screen_home
from ui import loading_screen   # <-- on importe la loading bar
from session_manager import ask_credentials

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_CYAN, -1)

    # Barre de chargement au démarrage
    loading_screen(stdscr)

    ask_credentials(stdscr)

    # Lancement de l'interface principale
    screen_home(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
