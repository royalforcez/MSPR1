import mysql.connector
from session_manager import DB_NTL, DB_ENTREPRISE

def get_db_data():
    """Récupère les données consolidées incluant le disque."""
    try:
        conn = mysql.connector.connect(**DB_NTL)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT 
            e.Nom, 
            e.IPv4, 
            o.nom_os AS OS,            
            r.CPU_Percent, 
            r.RAM_Usage_Percent, 
            r.disk_usage_percent, 
            r.uptime, 
            s.Nom as Site
        FROM tb_equipements e
        LEFT JOIN tb_sites s ON e.id_site = s.id
        LEFT JOIN tb_os o ON e.id_os = o.id
        LEFT JOIN tb_utilisation_ressources r ON r.ID = (
            SELECT MAX(ID) 
            FROM tb_utilisation_ressources 
            WHERE id_equipement = e.ID
        )
        WHERE e.est_actif = 1
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return f"Erreur de lecture : {str(e)}"

def check_db_health():
    """Vérifie le statut des deux bases de données."""
    results = {
        "ntl": (False, "Injoignable"),
        "entreprise": (False, "Injoignable")
    }

    # Test NTL
    try:
        conn = mysql.connector.connect(**DB_NTL, connect_timeout=2)
        if conn.is_connected():
            results["ntl"] = (True, "ONLINE (ntlsystools)")
            conn.close()
    except Exception as e:
        results["ntl"] = (False, f"Erreur : {str(e)[:20]}")

    # Test ENTREPRISE
    try:
        conn = mysql.connector.connect(**DB_ENTREPRISE, connect_timeout=2)
        if conn.is_connected():
            results["entreprise"] = (True, f"ONLINE ({DB_ENTREPRISE['database']})")
            conn.close()
    except Exception as e:
        results["entreprise"] = (False, f"Erreur : {str(e)[:20]}")

    return results

def get_services_data():
    """Récupère le dernier état AD/DNS, trié par nom de serveur (ex: DC01, DC02)."""
    statuses = {}
    try:
        from session_manager import DB_NTL
        import mysql.connector
        
        conn = mysql.connector.connect(**DB_NTL)
        cursor = conn.cursor(dictionary=True)
        
        
        query = """
        SELECT e.nom AS equipement, s.nom_service, s.etat
        FROM tb_etat_services s
        JOIN tb_equipements e ON s.id_equipement = e.id
        WHERE s.id IN (
            SELECT MAX(id) 
            FROM tb_etat_services 
            WHERE nom_service IN ('Active Directory', 'DNS')
            GROUP BY id_equipement, nom_service
        )
        ORDER BY e.nom, s.nom_service
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        
        for row in rows:
            server = row['equipement']
            service = row['nom_service']
            if server not in statuses:
                statuses[server] = {}
            statuses[server][service] = row['etat']
            
        cursor.close()
        conn.close()
    except Exception as e:
        pass
        
    return statuses