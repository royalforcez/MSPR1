import os
import mysql.connector
import smbclient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_auto_backup():
    print("    -> Préparation de la sauvegarde SQL...")
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'database': os.getenv('DB_NAME')
    }
    
    nas_config = {
        'ip': os.getenv('NAS_IP'),
        'share': os.getenv('NAS_SHARE'),
        'user': os.getenv('NAS_USER'),
        'password': os.getenv('NAS_PASS')
    }
    
    # 1. Sauvegarde SQL Locale
    backup_dir = "backups/sql"
    if not os.path.exists(backup_dir): 
        os.makedirs(backup_dir)
        
    filename = f"{backup_dir}/backup_{db_config['database']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"-- Backup SQL Complet\n-- Base : {db_config['database']}\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
            f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n\n")
            
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_table_sql = cursor.fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n{create_table_sql};\n\n")
                
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                if rows:
                    column_names = [i[0] for i in cursor.description]
                    cols_str = "`,`".join(column_names)
                    for row in rows:
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
        print(f"    -> [OK] Sauvegarde locale réussie : {filename}")
        
    except Exception as e:
        print(f"    -> [ERREUR] Échec de la sauvegarde locale : {e}")
        if 'conn' in locals() and conn.is_connected(): conn.close()
        return
        
    # 2. Envoi vers le NAS
    if not nas_config['ip']:
        print("    -> [ATTENTION] NAS_IP non défini dans le .env, l'envoi vers le NAS est ignoré.")
        return
        
    print("    -> Envoi de la sauvegarde vers le NAS en cours...")
    remote_path = f"\\\\{nas_config['ip']}\\{nas_config['share']}\\{os.path.basename(filename)}"
    try:
        smbclient.register_session(nas_config['ip'], username=nas_config['user'], password=nas_config['password'])
        with open(filename, 'rb') as local_f:
            with smbclient.open_file(remote_path, mode='wb') as remote_f:
                remote_f.write(local_f.read())
        print(f"    -> [OK] Envoi NAS réussi : {remote_path}")
    except Exception as e:
        print(f"    -> [ERREUR] Échec de l'envoi NAS : {e}")