import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )

def get_all_active_equipments():
    """Récupère UNIQUEMENT les machines actives (Soft Delete)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nom, ipv4, ssh_user, serial_number, id_os FROM tb_equipements WHERE est_actif = 1")
    equipments = cursor.fetchall()
    conn.close()
    return equipments

def add_equipment(nom, ip, ssh_user='ntl_monitor'):
    """Ajoute une machine avec est_actif = 1 par défaut"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tb_equipements WHERE ipv4 = %s", (ip,))
    if not cursor.fetchone():
        # Site 1 par défaut, Actif par défaut, OS NULL pour l'instant (sera détecté plus tard)
        sql = "INSERT INTO tb_equipements (nom, ipv4, ssh_user, id_site, est_actif) VALUES (%s, %s, %s, 1, 1)"
        cursor.execute(sql, (nom, ip, ssh_user))
        conn.commit()
        added = True
    else:
        added = False
    conn.close()
    return added

def get_or_create_os(nom_os, version_os):
    """Cherche l'OS dans tb_os, ou le crée s'il n'existe pas"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tb_os WHERE nom_os = %s AND version_os = %s", (nom_os, version_os))
    result = cursor.fetchone()
    
    if result:
        os_id = result[0]
    else:
        cursor.execute("INSERT INTO tb_os (nom_os, version_os) VALUES (%s, %s)", (nom_os, version_os))
        conn.commit()
        os_id = cursor.lastrowid
        
    conn.close()
    return os_id

def update_equipment_info(equip_id, nom, serial_number, id_os):
    """Met à jour le Nom, le Serial Number et le lien OS de la machine"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tb_equipements SET nom = %s, serial_number = %s, id_os = %s WHERE id = %s", 
                   (nom, serial_number, id_os, equip_id))
    conn.commit()
    conn.close()

def insert_metrics(equip_id, cpu, ram, disk, uptime):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO tb_utilisation_ressources (cpu_percent, ram_usage_percent, disk_usage_percent, uptime, id_equipement) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(sql, (cpu, ram, disk, uptime, equip_id))
    conn.commit()
    conn.close()

def insert_service_status(equip_id, service_name, status):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO tb_etat_services (nom_service, etat, id_equipement) VALUES (%s, %s, %s)"
    cursor.execute(sql, (service_name, status, equip_id))
    conn.commit()
    conn.close()