import curses
from ui import draw_frame
from diagnostic import screen_diagnostic
from wms_backup import screen_wms_backup
from obsolescence import screen_obsolescence_audit

MODULES = [
    "1. Module Diagnostic",
    "2. Module Sauvegarde WMS",
    "3. Module Audit d’Obsolescence",
    "Q. Quitter"
]

APP_NAME = [
    "███╗   ██╗████████╗██╗",
    "████╗  ██║╚══██╔══╝██║",
    "██╔██╗ ██║   ██║   ██║",
    "██║╚██╗██║   ██║   ██║",
    "██║ ╚████║   ██║   ███████╗",
    "╚═╝  ╚═══╝   ╚═╝   ╚══════╝",
    "███████╗██╗   ██╗███████╗",
    "██╔════╝╚██╗ ██╔╝██╔════╝",
    "███████╗ ╚████╔╝ ███████╗",
    "╚════██║  ╚██╔╝  ╚════██║",
    "███████║   ██║   ███████║",
    "╚══════╝   ╚═╝   ╚══════╝",
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
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        # Titre
        x_title = (w - max(len(l) for l in APP_NAME)) // 2
        stdscr.attron(curses.color_pair(3))
        for i, line in enumerate(APP_NAME):
            stdscr.addstr(i, x_title, line)
        stdscr.attroff(curses.color_pair(3))

        frame_top = len(APP_NAME) + 1
        draw_frame(stdscr, frame_top)

        for i, module in enumerate(MODULES):
            color = curses.color_pair(2 if i == current else 1)
            stdscr.attron(color)
            stdscr.addstr(frame_top + 2 + i, 4, module)
            stdscr.attroff(color)

        footer = "↑ ↓ naviguer | ENTER sélectionner | Q quitter"
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

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
