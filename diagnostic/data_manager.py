import mysql.connector
import logging
from session_manager import DB_NTL, DB_ENTREPRISE

def get_db_data():
    """Récupère les données consolidées. Retourne une liste (succès) ou un code erreur (int)."""
    conn = None
    try:
        # On tente la connexion avec un timeout court pour ne pas figer l'UI
        conn = mysql.connector.connect(**DB_NTL, connect_timeout=3)
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
        logging.info(f"Récupération de {len(rows)} équipements depuis la base NTL.")
        return rows

    except mysql.connector.Error as err:
        logging.error(f"Erreur SQL (get_db_data) : {err.msg} (Code: {err.errno})")
        return 1 # Code erreur pour problème SQL
    except Exception as e:
        logging.error(f"Erreur inattendue (get_db_data) : {str(e)}")
        return 2 # Autre erreur
    finally:
        if conn and conn.is_connected():
            conn.close()

def check_db_health():
    """Vérifie le statut des bases. Retourne un dict avec statuts et messages logués."""
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
        logging.warning(f"Santé NTL : ÉCHEC - {str(e)[:50]}")
        results["ntl"] = (False, f"Erreur : {str(e)[:20]}")

    # Test ENTREPRISE
    try:
        conn = mysql.connector.connect(**DB_ENTREPRISE, connect_timeout=2)
        if conn.is_connected():
            results["entreprise"] = (True, f"ONLINE ({DB_ENTREPRISE['database']})")
            conn.close()
    except Exception as e:
        logging.warning(f"Santé Entreprise : ÉCHEC - {str(e)[:50]}")
        results["entreprise"] = (False, f"Erreur : {str(e)[:20]}")

    return results

def get_services_data():
    """Récupère l'état AD/DNS. Retourne un dict (succès) ou un dict vide (échec)."""
    statuses = {}
    conn = None
    try:
        conn = mysql.connector.connect(**DB_NTL, connect_timeout=3)
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
        logging.info("Données des services AD/DNS récupérées.")
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des services : {e}")
        # On retourne un dict vide, le module de diagnostic saura qu'il n'y a rien à afficher
    finally:
        if conn and conn.is_connected():
            conn.close()
        
    return statuses