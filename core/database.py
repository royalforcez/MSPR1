import os
import mysql.connector
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )

def get_all_equipments():
    """Récupère la liste des machines à monitorer"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Remplacement de OS_Type et SSH_User par la colonne OS existante
    cursor.execute("SELECT ID, Nom, IPv4, OS, SSH_User FROM Equipements")
    equipments = cursor.fetchall()
    conn.close()
    return equipments

def add_equipment(nom, ip, os_name='Linux'):
    """Ajoute une nouvelle machine (utilisé par le scanner)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM Equipements WHERE IPv4 = %s", (ip,))
    if not cursor.fetchone():
        # Utilisation de la colonne OS
        sql = "INSERT INTO Equipements (Nom, IPv4, ID_Site, OS) VALUES (%s, %s, 1, %s)"
        cursor.execute(sql, (nom, ip, os_name))
        conn.commit()
        added = True
    else:
        added = False
    conn.close()
    return added

def insert_metrics(equip_id, cpu, ram, disk, uptime):
    """Pousse les ressources dans la BDD"""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO UtilisationRessources (CPU_Percent, RAM_Usage_Percent, Disk_Usage_Percent, uptime, ID_Equipement) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (cpu, ram, disk, uptime, equip_id))
    conn.commit()
    conn.close()

def insert_service_status(equip_id, service_name, status):
    """Pousse l'état d'un service"""
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO EtatServices (Nom_Service, Etat, ID_Equipement) VALUES (%s, %s, %s)"
    cursor.execute(sql, (service_name, status, equip_id))
    conn.commit()
    conn.close()

def update_equipment_name(equip_id, new_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Equipements SET Nom = %s WHERE ID = %s", (new_name, equip_id))
    conn.commit()
    conn.close()