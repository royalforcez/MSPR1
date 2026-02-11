import curses

def screen_wms_backup(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    title = "Module Sauvegarde WMS"

    stdscr.attron(curses.color_pair(3))
    stdscr.addstr(2, (w - len(title)) // 2, title)
    stdscr.attroff(curses.color_pair(3))

    stdscr.addstr(h // 2, (w - 48) // 2, "Ici tu mettras la logique de sauvegarde WMS")
    stdscr.addstr(h - 2, 2, "Appuie sur une touche pour revenir")
    stdscr.refresh()
    stdscr.getch()
