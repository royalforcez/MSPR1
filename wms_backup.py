import curses
import mysql.connector
import csv
import os
from datetime import datetime

# =========================================================
# LOGIQUE DYNAMIQUE
# =========================================================

def get_db_config():
    return {
        "host": "127.0.0.1",
        "user": "root",
        "password": "",
        "database": "ntlsystools"
    }

def get_all_tables():
    """Récupère dynamiquement la liste de toutes les tables de la BDD."""
    config = get_db_config()
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        # On extrait le premier élément de chaque tuple retourné
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception:
        return []

def backup_db_to_sql():
    """Génère un fichier .sql complet (Structure + Données) dynamiquement."""
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
                # Structure
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_sql = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{create_sql};\n\n")

                # Données
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
    """Exporte n'importe quelle table passée en paramètre en CSV."""
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
# INTERFACE CURSES DYNAMIQUE
# =========================================================

def screen_wms_backup(stdscr):
    stdscr.attrset(0)
    curses.curs_set(0)
    
    current_row = 0
    
    while True:
        # On récupère les tables à chaque rafraîchissement pour être à jour
        all_tables = get_all_tables()
        
        # Construction du menu
        options = ["💾 SAUVEGARDE COMPLÈTE (SQL)"] 
        options += [f"📄 EXPORT CSV : {t}" for t in all_tables]
        options.append("🚪 RETOUR")

        stdscr.erase()
        h, w = stdscr.getmaxyx()
        
        # Titre
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(1, (w-35)//2, " 📦 GESTION DES DONNÉES DYNAMIQUE ")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

        # Affichage des options (avec gestion du scroll si trop de tables)
        for i, opt in enumerate(options):
            if 4 + i < h - 5: # Empêche de déborder de l'écran
                style = curses.A_REVERSE if i == current_row else 0
                stdscr.addstr(4 + i, 4, opt, style)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP: current_row = (current_row - 1) % len(options)
        elif key == curses.KEY_DOWN: current_row = (current_row + 1) % len(options)
        elif key in [10, 13, curses.KEY_ENTER]:
            
            # Action : Backup SQL
            if current_row == 0:
                stdscr.addstr(h-4, 4, "⏳ Création du SQL...", curses.color_pair(3))
                stdscr.refresh()
                success, msg = backup_db_to_sql()
            
            # Action : Retour
            elif current_row == len(options) - 1:
                break
            
            # Action : Export CSV d'une table
            else:
                table_to_export = all_tables[current_row - 1]
                stdscr.addstr(h-4, 4, f"⏳ Export de {table_to_export}...", curses.color_pair(3))
                stdscr.refresh()
                success, msg = export_table_to_csv(table_to_export)

            # Résultat
            stdscr.move(h-4, 0); stdscr.clrtobot()
            if success:
                stdscr.addstr(h-4, 4, "✅ TERMINÉ !", curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(h-3, 4, f"Fichier : {os.path.basename(msg)}", curses.A_DIM)
            else:
                stdscr.addstr(h-4, 4, "❌ ERREUR", curses.color_pair(4) | curses.A_BOLD)
                stdscr.addstr(h-3, 4, f"Détail : {msg[:w-15]}")
            
            stdscr.addstr(h-2, 4, "Appuyez sur une touche...")
            stdscr.getch()

        elif key == 27: break

    stdscr.clear()