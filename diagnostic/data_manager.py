import mysql.connector

def get_db_data():
    """Récupère les données consolidées selon le nouveau schéma MariaDB."""
    try:
        conn = mysql.connector.connect(
            host="192.168.1.137",
            user="admin_ntl",
            password="Formation2025",
            database="ntlsystools",
            connect_timeout=2  # Augmenté légèrement pour la stabilité
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # On utilise MAX(r.ID) ou un tri pour ne prendre que la dernière ressource connue
        query = """
        SELECT 
            e.Nom, 
            e.IPv4, 
            eol.OS, 
            eol.Version, 
            r.CPU_Percent, 
            r.RAM_Usage_Percent, 
            r.uptime, 
            s.Nom as Site
        FROM Equipements e
        LEFT JOIN EndOfLife eol ON e.ID_EOL = eol.ID
        LEFT JOIN Sites s ON e.ID_Site = s.ID
        -- Jointure sur la dernière entrée de ressources uniquement
        LEFT JOIN UtilisationRessources r ON r.ID = (
            SELECT MAX(ID) 
            FROM UtilisationRessources 
            WHERE ID_Equipement = e.ID
        )
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        return f"Erreur de lecture : {str(e)}"

def check_db_health():
    """Vérifie si le serveur MariaDB répond."""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="ntlsystools",
            connect_timeout=1
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            # On peut aussi vérifier si les tables existent
            cursor.execute("SHOW TABLES LIKE 'Equipements'")
            exists = cursor.fetchone()
            conn.close()
            
            if exists:
                return True, "MariaDB OK (Base ntlsystools prête)"
            else:
                return False, "MariaDB Connecté mais tables manquantes"
    except Exception as e:
        return False, f"SQL Injoignable : {str(e)}"