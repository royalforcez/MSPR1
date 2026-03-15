import curses
import mysql.connector
import csv
import os
from datetime import datetime

# =========================================================
# LOGIQUE DE CONNEXION (Inchangée)
# =========================================================

def get_db_config():
    return {
        "host": "192.168.1.137",
        "user": "admin_ntl",
        "password": "Formation2025",
        "database": "ntlsystools"
    }

def get_all_tables():
    config = get_db_config()
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception:
        return []

# --- Fonctions de sauvegarde SQL et CSV (Inchangées) ---

def backup_db_to_sql():
    config = get_db_config()
    backup_dir = "backups/sql"
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)
    filename = f"{backup_dir}/backup_{config['database']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    tables = get_all_tables()
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup SQL Automatique\n-- Date: {datetime.now()}\n\n")
            f.write(f"CREATE DATABASE IF NOT EXISTS `{config['database']}`;\n")
            f.write(f"USE `{config['database']}`;\n\n")
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_sql = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{create_sql};\n\n")
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                if rows:
                    f.write(f"INSERT INTO `{table}` VALUES \n")
                    vals = []
                    for r in rows:
                        clean = ["NULL" if v is None else (str(v) if isinstance(v, (int, float)) else f"'{str(v).replace("'", "''")}'") for v in r]
                        vals.append("(" + ", ".join(clean) + ")")
                    f.write(",\n".join(vals) + ";\n\n")
        conn.close()
        return True, filename
    except Exception as e:
        return False, str(e)

def export_table_to_csv(table_name):
    config = get_db_config()
    backup_dir = "backups/csv"
    if not os.path.exists(backup_dir): os.makedirs(backup_dir)
    filename = f"{backup_dir}/export_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        conn = mysql.connector.connect(**config)
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
# INTERFACE GRAPHIQUE OPTIMISÉE (ZÉRO LAG)
# =========================================================

def screen_wms_backup(stdscr):
    # --- ÉTAPE 1 : On récupère les tables UNE SEULE FOIS au début ---
    stdscr.clear()
    stdscr.addstr(2, 4, "⏳ Connexion à la base de données...", curses.color_pair(3))
    stdscr.refresh()
    all_tables = get_all_tables()
    
    current = 0

    while True:
        stdscr.attrset(0)
        stdscr.clear()

        curses.init_pair(1, curses.COLOR_WHITE, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

        h, w = stdscr.getmaxyx()
        
        title = "Module Gestion des Sauvegardes (WMS)"
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(2, (w - len(title)) // 2, title)
        stdscr.attroff(curses.color_pair(3))

        # --- ÉTAPE 2 : On utilise la variable all_tables déjà chargée ---
        MODULES = ["SAUVEGARDE COMPLÈTE (SQL)"]
        MODULES += [f"EXPORT CSV : {t}" for t in all_tables]
        MODULES.append("RETOUR (HOME)")

        for i, module in enumerate(MODULES):
            cp = curses.color_pair(2 if i == current else 1)
            stdscr.attrset(cp)
            if i == current:
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(6 + i, 4, f"> {module}")
                stdscr.attroff(curses.A_BOLD)
            else:
                stdscr.addstr(6 + i, 4, f"  {module}")

        footer = "↑ ↓ naviguer | ENTER sélectionner | R rafraîchir | ESC: Home"
        stdscr.attrset(curses.color_pair(1))
        stdscr.addstr(h - 1, (w - len(footer)) // 2, footer)

        stdscr.refresh()
        key = stdscr.getch()

        # Navigation (Instantanée maintenant)
        if key == curses.KEY_UP and current > 0:
            current -= 1
        elif key == curses.KEY_DOWN and current < len(MODULES) - 1:
            current += 1
        
        # Action Manuelle de Rafraîchissement (Touche R)
        elif key in (ord('r'), ord('R')):
            stdscr.clear()
            stdscr.addstr(5, 4, "⏳ Rafraîchissement des tables...", curses.color_pair(3))
            stdscr.refresh()
            all_tables = get_all_tables()
            current = 0

        # Actions (Touche Entrée)
        elif key in (10, 13):
            if current == len(MODULES) - 1:
                return

            elif current == 0:
                stdscr.clear()
                stdscr.addstr(5, 4, "⏳ Génération du backup SQL complet...", curses.color_pair(3))
                stdscr.refresh()
                success, path = backup_db_to_sql()
                
                stdscr.move(7, 0)
                if success:
                    stdscr.addstr(7, 4, "✅ Sauvegarde terminée", curses.color_pair(2))
                    stdscr.addstr(8, 4, f"Fichier : {os.path.basename(path)}", curses.color_pair(1))
                else:
                    stdscr.addstr(7, 4, "❌ Erreur SQL", curses.color_pair(1))
                    stdscr.addstr(8, 4, str(path)[:w-10])
                
                stdscr.addstr(10, 4, "Appuie sur une touche pour continuer")
                stdscr.getch()

            else:
                table_name = all_tables[current - 1]
                stdscr.clear()
                stdscr.addstr(5, 4, f"⏳ Exportation de {table_name}...", curses.color_pair(3))
                stdscr.refresh()
                success, path = export_table_to_csv(table_name)
                
                if success:
                    stdscr.addstr(7, 4, "✅ Export terminé", curses.color_pair(2))
                    stdscr.addstr(8, 4, f"Fichier : {os.path.basename(path)}", curses.color_pair(1))
                else:
                    stdscr.addstr(7, 4, "❌ Erreur Export CSV", curses.color_pair(1))
                    stdscr.addstr(8, 4, str(path)[:w-10])
                
                stdscr.addstr(10, 4, "Appuie sur une touche pour continuer")
                stdscr.getch()

        elif key == 27:
            return