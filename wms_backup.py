import curses
import mysql.connector
import csv
import os
import smbclient
import time
from datetime import datetime
from session_manager import DB_NTL, DB_ENTREPRISE, NAS_CONFIG

# =========================================================
# CONFIGURATIONS
# =========================================================

def get_available_databases():
    return [
        {"display": f"💻 BASE NTL (TP) - {DB_NTL['host']}", "config": DB_NTL},
        {"display": f"🏢 BASE ENTREPRISE (PROD) - {DB_ENTREPRISE['host']}", "config": DB_ENTREPRISE}
    ]

def get_nas_config():
    return NAS_CONFIG

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

def backup_db_to_sql(db_config, stdscr=None):
    """Sauvegarde complète avec retour visuel sur stdscr"""
    backup_dir = "backups/sql"
    if not os.path.exists(backup_dir): 
        os.makedirs(backup_dir)
    
    filename = f"{backup_dir}/backup_{db_config['database']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    spinner = ["|", "/", "-", "\\"]
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        total_tables = len(tables)

        with open(filename, 'w', encoding='utf-8') as f:
            # Entête propre pour éviter les erreurs de syntaxe à l'import
            f.write(f"-- Backup SQL Complet\n-- Base : {db_config['database']}\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
            f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n\n")

            for index, table in enumerate(tables):
                # --- MISE À JOUR VISUELLE ---
                if stdscr:
                    percent = int((index / total_tables) * 100)
                    stdscr.move(10, 4)
                    stdscr.clrtoeol()
                    stdscr.addstr(10, 4, f"📊 Progression : [{percent}%] Traitement de : {table}...", curses.color_pair(3))
                    stdscr.refresh()

                # --- STRUCTURE ---
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table_sql = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{create_table_sql};\n\n")
                
                # --- DONNÉES ---
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                
                if rows:
                    column_names = [i[0] for i in cursor.description]
                    cols_str = "`,`".join(column_names)
                    
                    for r_idx, row in enumerate(rows):
                        # Animation spinner pour les grosses tables
                        if stdscr and r_idx % 50 == 0:
                            stdscr.addstr(10, 60, f" {spinner[r_idx // 50 % 4]}")
                            stdscr.refresh()

                        values = []
                        for val in row:
                            if val is None: values.append("NULL")
                            elif isinstance(val, (int, float)): values.append(str(val))
                            elif hasattr(val, 'isoformat'): values.append(f"'{val}'")
                            else:
                                clean_val = str(val).replace("'", "''").replace("\\", "\\\\")
                                values.append(f"'{clean_val}'")
                        
                        f.write(f"INSERT INTO `{table}` (`{cols_str}`) VALUES ({', '.join(values)});\n")
                    f.write("\n")

            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            
        conn.close()
        return True, filename

    except Exception as e:
        if 'conn' in locals() and conn.is_connected(): conn.close()
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
# INTERFACES
# =========================================================

def select_database_prompt(stdscr):
    dbs = get_available_databases()
    h, w = stdscr.getmaxyx()
    win_h, win_w = 10, 65
    start_y, start_x = (h - win_h) // 2, (w - win_w) // 2
    win = curses.newwin(win_h, win_w, start_y, start_x)
    win.box(); win.keypad(True)
    
    choice = 0
    while True:
        win.attron(curses.color_pair(3))
        win.addstr(1, (win_w - 32) // 2, " SÉLECTION DE LA SOURCE SQL ", curses.A_BOLD)
        win.attroff(curses.color_pair(3))
        
        for i, db in enumerate(dbs):
            style = curses.color_pair(2) | curses.A_REVERSE if i == choice else curses.A_NORMAL
            win.addstr(4 + i, 4, f" {db['display']} ", style)
        
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
            style = curses.color_pair(2) | curses.A_REVERSE if i == choice else curses.A_NORMAL
            win.addstr(4 + i, 4, opt, style)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP: choice = 0
        elif key == curses.KEY_DOWN: choice = 1
        elif key in (10, 13): return "local" if choice == 0 else "nas"
        elif key == 27: return None

# =========================================================
# MODULE PRINCIPAL
# =========================================================

def screen_wms_backup(stdscr):
    selected_db_config = select_database_prompt(stdscr)
    if not selected_db_config: return 

    stdscr.clear()
    h, w = stdscr.getmaxyx() 
    stdscr.addstr(h//2, (w-30)//2, "⏳ Connexion à la base...", curses.color_pair(3))
    stdscr.refresh()
    
    all_tables = []
    try:
        conn = mysql.connector.connect(**selected_db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        stdscr.addstr(h//2 + 2, 4, f"❌ Erreur : {str(e)}", curses.color_pair(1))
        stdscr.getch(); return

    current = 0
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        title = f"SAUVEGARDES : {selected_db_config['database'].upper()}"
        stdscr.addstr(2, (w - len(title)) // 2, title, curses.color_pair(3) | curses.A_BOLD)

        MODULES = ["SAUVEGARDE COMPLÈTE (SQL + DATA)"] + [f"CSV : {t}" for t in all_tables] + ["RETOUR"]

        for i, module in enumerate(MODULES):
            if i == current:
                stdscr.addstr(6 + i, 4, f"> {module}", curses.color_pair(2) | curses.A_BOLD)
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
            stdscr.addstr(5, 4, "⏳ INITIALISATION...", curses.color_pair(3))
            stdscr.refresh()

            if current == 0:
                # APPEL AVEC STDSCR POUR LA BARRE DE PROGRESSION
                success, path = backup_db_to_sql(selected_db_config, stdscr)
            else:
                table_name = all_tables[current - 1]
                stdscr.addstr(7, 4, f"📄 Exportation CSV : {table_name}...")
                stdscr.refresh()
                success, path = export_table_to_csv(table_name, selected_db_config)

            if success and dest == "nas":
                stdscr.addstr(12, 4, "📡 Envoi vers le NAS...", curses.color_pair(3))
                stdscr.refresh()
                nas_ok, nas_res = save_to_nas(path)
                if nas_ok: path = nas_res
                else: success = False; path = f"Erreur NAS: {nas_res}"

            # Résultat
            stdscr.addstr(15, 4, "✅ RÉUSSI" if success else "❌ ÉCHEC", curses.color_pair(2 if success else 1) | curses.A_BOLD)
            stdscr.addstr(16, 4, f"Fichier : {path}")
            stdscr.addstr(18, 4, "Appuyez sur une touche...")
            stdscr.getch()
        elif key == 27: return