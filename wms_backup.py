import curses
import mysql.connector
import csv
import os
import smbclient
import time
import logging
import json
from datetime import datetime
from decimal import Decimal

# Import des constantes
try:
    from session_manager import DB_NTL, DB_ENTREPRISE, NAS_CONFIG
except ImportError:
    logging.error("Impossible de charger session_manager.")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal): return float(obj)
        return super(DecimalEncoder, self).default(obj)

# =========================================================
# LOGIQUE DE SAUVEGARDE ET TRANSFERT
# =========================================================

def export_table_to_csv(table_name, db_config):
    """Exporte une table specifique en format CSV avec logs d'audit."""
    backup_dir = "backups/csv"
    if not os.path.exists(backup_dir): 
        os.makedirs(backup_dir)
    
    filename = f"{backup_dir}/export_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    try:
        logging.info(f"Debut export CSV table : {table_name}")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table_name}`")
        rows = cursor.fetchall()
        
        if not rows:
            logging.warning(f"Export CSV annule : La table '{table_name}' est vide.")
            conn.close()
            return False, f"Table '{table_name}' vide."
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
            
        nb_lignes = len(rows)
        logging.info(f"Export CSV reussi : {filename} ({nb_lignes} lignes)")
        conn.close()
        return True, filename

    except Exception as e:
        logging.error(f"Erreur critique Export CSV ({table_name}) : {e}", exc_info=True)
        return False, str(e)

def save_to_nas(local_file_path):
    """Transfere un fichier vers le partage SMB du NAS."""
    config = NAS_CONFIG
    filename = os.path.basename(local_file_path)
    remote_path = f"\\\\{config['ip']}\\{config['share']}\\{filename}"
    
    try:
        logging.info(f"Transfert NAS en cours : {filename}")
        smbclient.register_session(config['ip'], username=config['user'], password=config['password'])
        
        with open(local_file_path, 'rb') as local_f:
            with smbclient.open_file(remote_path, mode='wb') as remote_f:
                remote_f.write(local_f.read())
        
        logging.info(f"Succes NAS : {remote_path}")
        return True, remote_path
    except Exception as e:
        logging.error(f"Echec NAS : {e}")
        return False, str(e)

def backup_db_to_sql(db_config, stdscr=None):
    """Genere un dump SQL complet avec suivi de progression et logs."""
    backup_dir = "backups/sql"
    if not os.path.exists(backup_dir): 
        os.makedirs(backup_dir)
    
    db_name = db_config.get('database', 'unknown')
    filename = f"{backup_dir}/backup_{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    spinner = ["|", "/", "-", "\\"]
    
    try:
        logging.info(f"Lancement Backup SQL complet de la base : {db_name}")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        total_tables = len(tables)

        if total_tables == 0:
            logging.warning(f"Backup SQL : Aucune table trouvee dans la base '{db_name}'.")
            conn.close()
            return False, "Base de donnees vide."

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup SQL Systoolbox\n-- Base : {db_name}\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            for index, table in enumerate(tables):
                if stdscr:
                    percent = int(((index + 1) / total_tables) * 100)
                    stdscr.move(10, 4)
                    stdscr.clrtoeol()
                    stdscr.addstr(10, 4, f"PROGRESSION : [{percent}%] Table : {table}", curses.color_pair(3))
                    stdscr.refresh()

                # Structure
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{cursor.fetchone()[1]};\n\n")
                
                # Donnees
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                
                if rows:
                    column_names = [i[0] for i in cursor.description]
                    cols_str = "`,`".join(column_names)
                    for r_idx, row in enumerate(rows):
                        if stdscr and r_idx % 100 == 0:
                            stdscr.addstr(10, 65, f" {spinner[r_idx // 100 % 4]}")
                            stdscr.refresh()

                        values = []
                        for val in row:
                            if val is None: values.append("NULL")
                            elif isinstance(val, (int, float, Decimal)): values.append(str(val))
                            else:
                                clean_val = str(val).replace("'", "''").replace("\\", "\\\\")
                                values.append(f"'{clean_val}'")
                        f.write(f"INSERT INTO `{table}` (`{cols_str}`) VALUES ({', '.join(values)});\n")
                    f.write("\n")
                else:
                    logging.info(f"Backup SQL : Table '{table}' ignoree (vide).")

            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            
        logging.info(f"Backup SQL termine avec succes : {filename}")
        conn.close()
        return True, filename

    except Exception as e:
        logging.error(f"Echec Backup SQL base {db_name} : {e}", exc_info=True)
        return False, str(e)

# =========================================================
# INTERFACES
# =========================================================

def select_database_prompt(stdscr):
    dbs = [
        {"display": f"BASE NTL (TP) - {DB_NTL['host']}", "config": DB_NTL},
        {"display": f"BASE ENTREPRISE (PROD) - {DB_ENTREPRISE['host']}", "config": DB_ENTREPRISE}
    ]
    h, w = stdscr.getmaxyx()
    win_h, win_w = 10, 65
    win = curses.newwin(win_h, win_w, (h - win_h) // 2, (w - win_w) // 2)
    win.box(); win.keypad(True)
    
    choice = 0
    while True:
        win.addstr(1, (win_w - 24) // 2, " SELECTION SOURCE SQL ", curses.color_pair(3) | curses.A_BOLD)
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
    win = curses.newwin(win_h, win_w, (h - win_h) // 2, (w - win_w) // 2)
    win.box(); win.keypad(True)
    choice = 0
    options = [" SAUVEGARDE LOCALE ", " TRANSFERT VERS LE NAS "]
    while True:
        win.addstr(1, (win_w - 20) // 2, " DESTINATION FLUX ", curses.color_pair(3) | curses.A_BOLD)
        for i, opt in enumerate(options):
            style = curses.color_pair(2) | curses.A_REVERSE if i == choice else curses.A_NORMAL
            win.addstr(4 + i, 4, opt, style)
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP: choice = 0
        elif key == curses.KEY_DOWN: choice = 1
        elif key in (10, 13): return "local" if choice == 0 else "nas"
        elif key == 27: return None

def screen_wms_backup(stdscr):
    selected_db_config = select_database_prompt(stdscr)
    if not selected_db_config: return 0

    stdscr.clear()
    h, w = stdscr.getmaxyx() 
    stdscr.addstr(h//2, (w-25)//2, "Connexion SQL en cours...", curses.color_pair(3))
    stdscr.refresh()
    
    try:
        conn = mysql.connector.connect(**selected_db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        logging.error(f"Erreur connexion : {e}")
        stdscr.addstr(h//2 + 2, 4, f"ERREUR : {str(e)}", curses.color_pair(1))
        stdscr.getch(); return 1

    current = 0
    while True:
        stdscr.clear()
        title = f"GESTION SAUVEGARDES : {selected_db_config['database'].upper()}"
        stdscr.addstr(2, (w - len(title)) // 2, title, curses.color_pair(3) | curses.A_BOLD)

        MENU = ["BACKUP COMPLET (SQL)"] + [f"EXPORT CSV : {t}" for t in all_tables] + ["RETOUR"]

        for i, item in enumerate(MENU):
            if i == current:
                stdscr.addstr(5 + i, 4, f"> {item}", curses.color_pair(2) | curses.A_BOLD)
            else:
                stdscr.addstr(5 + i, 4, f"  {item}")

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current > 0: current -= 1
        elif key == curses.KEY_DOWN and current < len(MENU) - 1: current += 1
        elif key in (10, 13):
            if current == len(MENU) - 1: return 0

            dest = ask_destination(stdscr)
            if not dest: continue

            stdscr.clear()
            stdscr.addstr(5, 4, "TRAITEMENT EN COURS...", curses.color_pair(3))
            stdscr.refresh()

            if current == 0:
                # Appel de la fonction SQL locale
                success, path = backup_db_to_sql(selected_db_config, stdscr)
            else:
                # Appel de la fonction CSV locale (plus d'import externe erroné)
                table_name = all_tables[current - 1]
                success, path = export_table_to_csv(table_name, selected_db_config)

            if success and dest == "nas":
                stdscr.addstr(12, 4, "TRANSFERT NAS LILLE...", curses.color_pair(3))
                stdscr.refresh()
                nas_ok, nas_res = save_to_nas(path)
                if nas_ok: path = nas_res
                else: success = False; path = f"ERR NAS: {nas_res}"

            stdscr.clear()
            res_txt = "SUCCES" if success else "ECHEC"
            stdscr.addstr(h//2 - 2, 4, f"RESULTAT : {res_txt}", curses.color_pair(2 if success else 1) | curses.A_BOLD)
            stdscr.addstr(h//2, 4, f"Cible : {path}")
            stdscr.addstr(h//2 + 2, 4, "Pressez une touche...")
            stdscr.getch()
            
        elif key == 27: # ESC
            return 0