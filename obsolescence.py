import curses

def screen_obsolescence_audit(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    title = "Module Audit d’Obsolescence"

    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(2, (w - len(title)) // 2, title)
    stdscr.attroff(curses.color_pair(3))

    stdscr.addstr(h // 2, (w - 54) // 2, "Ici tu mettras la logique d’audit d’obsolescence")
    stdscr.addstr(h - 2, 2, "Appuie sur une touche pour revenir")
    stdscr.refresh()
    stdscr.getch()

