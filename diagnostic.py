import curses

def screen_diagnostic(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    title = "Module Diagnostic"

    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(2, (w - len(title)) // 2, title)
    stdscr.attroff(curses.color_pair(3))

    stdscr.addstr(h // 2, (w - 40) // 2, "Ici tu mettras la logique du diagnostic")
    stdscr.addstr(h - 2, 2, "Appuie sur une touche pour revenir")
    stdscr.refresh()
    stdscr.getch()
