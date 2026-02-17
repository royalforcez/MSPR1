import mysql.connector
import os
import platform
import socket

DB_CONFIG = {
    'host': 'localhost',
    'user': 'admin_ntl',
    'password': 'Formation2025',
    'database': 'ntlsystools'
}

def check_ping(ip):
    """Vérifie si la machine répond au ping"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', ip]
    return os.system(" ".join(command)) == 0

def check_service_port(ip, port):
    """Vérifie si un port spécifique est ouvert (ex: 3306 pour MySQL)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, port))
        return "UP"
    except:
        return "DOWN"
    finally:
        s.close()

def run_centralized_feeder():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True) # On récupère les résultats sous forme de dictionnaire

        # 1. On va chercher la liste des machines à "interroger"
        cursor.execute("SELECT ID, Nom, IPv4 FROM Equipements")
        hosts = cursor.fetchall()

        for host in hosts:
            print(f"--- Scan de {host['Nom']} ({host['IPv4']}) ---")
            
            # 2. Test de présence (Ping)
            is_alive = check_ping(host['IPv4'])
            
            # 3. Test des services (Exemple : DNS sur 53, MySQL sur 3306)
            dns_status = check_service_port(host['IPv4'], 53)
            mysql_status = check_service_port(host['IPv4'], 3306)

            # 4. Insertion des états dans la BDD
            sql = "INSERT INTO EtatServices (Nom_Service, Etat, ID_Equipement) VALUES (%s, %s, %s)"
            cursor.execute(sql, ("DNS", dns_status, host['ID']))
            cursor.execute(sql, ("MySQL", mysql_status, host['ID']))
            
            # Note : Pour le CPU/RAM à distance, cela demandera 
            # une connexion SSH ou un agent local plus tard.
            
        conn.commit()
        print("\nScan terminé et BDD mise à jour.")

    except mysql.connector.Error as err:
        print(f"Erreur : {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_centralized_feeder()