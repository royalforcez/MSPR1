import curses
import time

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)   # normal
    curses.init_pair(2, curses.COLOR_GREEN, -1)   # selected
    curses.init_pair(3, curses.COLOR_CYAN, -1)    # title

def loading_screen(stdscr):
    h, w = stdscr.getmaxyx()
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

        # Logo SysToolbox
        stdscr.attron(curses.color_pair(3))
        for idx, line in enumerate(logo):
            stdscr.addstr(start_y + idx, logo_x, line)
        stdscr.attroff(curses.color_pair(3))

        # Texte
        title = "Chargement des modules..."
        stdscr.addstr(start_y + logo_height + 1, (w - len(title)) // 2, title)

        # Barre de chargement █░
        bar = "█" * i + "░" * (bar_width - i)
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(start_y + logo_height + 3, (w - bar_width - 2) // 2, f"[{bar}]")
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()
        time.sleep(0.012)





def draw_frame(stdscr, top):
    h, w = stdscr.getmaxyx()
    bottom = h - 2

    if bottom <= top + 2:
        return

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
