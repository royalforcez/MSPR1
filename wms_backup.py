import curses
import mysql.connector
import csv
import os
import smbclient
from datetime import datetime

# =========================================================
# CONFIGURATIONS
# =========================================================

def get_available_databases():
    """ Liste des bases de données disponibles avec leurs configs respectives """
    return [
        {
            "display": "💻 BASE DE DONNÉES TP (ntlsystools)",  # base de donnée ntl
            "config": {
                "host": "192.168.1.137",
                "user": "admin_ntl",
                "password": "Formation2025",
                "database": "ntlsystools"
            }
        },
        {
            "display": "🏢 BASE DE DONNÉES ENTREPRISE (prod_wms)", # base de donnéee de l'entreprise
            "config": {
                "host": "127.0.0.1", # À modifier si l'IP est différente
                "user": "root",
                "password": "",
                "database": "prod_wms"
            }
        }
    ]

def get_nas_config():
    """ Configuration pour le NAS de Lille """
    return {
        "ip": "192.168.1.11", # ip du nas à rensigner 
        "user": "admin_ntl", # identifiant à rensigner
        "password": "Formation2025",
        "share": "NAS-Lille" # non du folder partager par le nas
    }

# =========================================================
# LOGIQUE DE SAUVEGARDE ET TRANSFERT
# =========================================================

def save_to_nas(local_file_path):
    config = get_nas_config()
    filename = os.path.basename(local_file_path)
    remote_path = f"\\\\{config['ip']}\\{config['share']}\\{filename}"
    try:
        smbclient.register_session(config['ip'], username=config['user'], password=config['password'])
        with open(local_file_path, 'rb') as local_f:
            with smbclient.open_file(remote_path, mode='wb') as remote_f:
                remote_f.write(local_f.read())
        return True, remote_path
    except Exception as e:
        return False, str(e)

def backup_db_to_sql(db_config):
    backup_dir = "backups/sql"
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)
    filename = f"{backup_dir}/backup_{db_config['database']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup SQL Automatique\n-- Base: {db_config['database']}\n\n")
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{cursor.fetchone()[1]};\n\n")
        conn.close()
        return True, filename
    except Exception as e:
        return False, str(e)

def export_table_to_csv(table_name, db_config):
    backup_dir = "backups/csv"
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)
    filename = f"{backup_dir}/export_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        if not rows: return False, "Table vide."
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        conn.close()
        return True, filename
    except Exception as e:
        return False, str(e)

# =========================================================
# INTERFACES DE SÉLECTION (POP-UPS)
# =========================================================

def select_database_prompt(stdscr):
    """ Demande à l'utilisateur quelle BDD utiliser au démarrage du module """
    dbs = get_available_databases()
    h, w = stdscr.getmaxyx()
    win_h, win_w = 10, 60
    start_y, start_x = (h - win_h) // 2, (w - win_w) // 2
    
    win = curses.newwin(win_h, win_w, start_y, start_x)
    win.box()
    win.keypad(True)
    
    choice = 0
    while True:
        win.attron(curses.color_pair(3))
        win.addstr(1, (win_w - 28) // 2, " SÉLECTION DE LA BASE DE DONNÉES ", curses.A_BOLD)
        win.attroff(curses.color_pair(3))
        win.addstr(3, 2, "Quelle base souhaitez-vous auditer / sauvegarder ?")
        
        for i, db in enumerate(dbs):
            if i == choice:
                win.attron(curses.color_pair(2) | curses.A_REVERSE)
                win.addstr(5 + i, 4, f" {db['display']} ")
                win.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                win.addstr(5 + i, 4, f" {db['display']} ")
        
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP: choice = (choice - 1) % len(dbs)
        elif key == curses.KEY_DOWN: choice = (choice + 1) % len(dbs)
        elif key in (10, 13): return dbs[choice]['config']
        elif key == 27: return None

def ask_destination(stdscr):
    h, w = stdscr.getmaxyx()
    win_h, win_w = 9, 50
    start_y, start_x = (h - win_h) // 2, (w - win_w) // 2
    win = curses.newwin(win_h, win_w, start_y, start_x)
    win.box(); win.keypad(True)
    choice = 0
    options = [" 💾  SAUVEGARDE LOCALE ", " 🌐  ENVOYER VERS LE NAS (LILLE) "]
    while True:
        win.addstr(1, (win_w - 22) // 2, " DESTINATION DU FLUX ", curses.color_pair(3) | curses.A_BOLD)
        for i, opt in enumerate(options):
            if i == choice:
                win.attron(curses.color_pair(2) | curses.A_REVERSE)
                win.addstr(5 + i, 4, opt)
                win.attroff(curses.color_pair(2) | curses.A_REVERSE)
            else:
                win.addstr(5 + i, 4, opt)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP: choice = 0
        elif key == curses.KEY_DOWN: choice = 1
        elif key in (10, 13): return "local" if choice == 0 else "nas"
        elif key == 27: return None

# =========================================================
# MODULE PRINCIPAL WMS
# =========================================================

def screen_wms_backup(stdscr):
    # --- ÉTAPE 1 : Choix de la BDD avant toute chose ---
    selected_db_config = select_database_prompt(stdscr)
    if not selected_db_config: return # Retour au menu principal si ESC

    # --- ÉTAPE 2 : Chargement des tables de la BDD choisie ---
    stdscr.clear()
    
    # AJOUTE CETTE LIGNE ICI POUR FIXER L'ERREUR :
    h, w = stdscr.getmaxyx() 
    
    stdscr.addstr(h//2, (w-30)//2, f"⏳ Chargement de {selected_db_config['database']}...", curses.color_pair(3))
    stdscr.refresh()
    
    all_tables = []
    try:
        conn = mysql.connector.connect(**selected_db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        # Gérer l'erreur si la BDD n'est pas accessible
        stdscr.clear()
        stdscr.addstr(5, 4, f"❌ Impossible de se connecter à {selected_db_config['database']}", curses.color_pair(1))
        stdscr.addstr(6, 4, str(e))
        stdscr.getch()
        return

    current = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Rappel de la BDD active dans le titre
        title = f"SAUVEGARDES : {selected_db_config['database'].upper()}"
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        MODULES = ["SAUVEGARDE COMPLÈTE (SQL)"]
        MODULES += [f"EXPORT CSV : {t}" for t in all_tables]
        MODULES.append("RETOUR / CHANGER DE BDD")

        for i, module in enumerate(MODULES):
            if i == current:
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(6 + i, 4, f"> {module}")
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            else:
                stdscr.addstr(6 + i, 4, f"  {module}")

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0: current -= 1
        elif key == curses.KEY_DOWN and current < len(MODULES) - 1: current += 1
        
        elif key in (10, 13):
            if current == len(MODULES) - 1: return 

            dest = ask_destination(stdscr)
            if not dest: continue

            stdscr.clear()
            stdscr.addstr(5, 4, "⏳ Traitement en cours...", curses.color_pair(3))
            stdscr.refresh()

            # On passe la config sélectionnée aux fonctions
            if current == 0:
                success, path = backup_db_to_sql(selected_db_config)
            else:
                success, path = export_table_to_csv(all_tables[current - 1], selected_db_config)

            if success and dest == "nas":
                stdscr.addstr(7, 4, "📡 Envoi vers le NAS de Lille...")
                stdscr.refresh()
                nas_ok, nas_res = save_to_nas(path)
                if nas_ok: path = nas_res
                else: success = False; path = f"Erreur NAS: {nas_res}"

            stdscr.move(10, 0)
            if success:
                stdscr.addstr(10, 4, f"✅ RÉUSSI ({dest.upper()})", curses.color_pair(2))
                stdscr.addstr(11, 4, f"Fichier : {os.path.basename(path)}")
            else:
                stdscr.addstr(10, 4, "❌ ÉCHEC", curses.color_pair(1))
                stdscr.addstr(11, 4, str(path))
            
            stdscr.addstr(13, 4, "Appuyez sur une touche...")
            stdscr.getch()

        elif key == 27: return