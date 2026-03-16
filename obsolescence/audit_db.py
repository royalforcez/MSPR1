import mysql.connector
from .models import Asset
from session_manager import DB_NTL  # On importe la config saisie au démarrage

def fetch_assets_from_db():
    """
    Récupère les machines depuis la base MySQL en utilisant la session active.
    """
    try:
        # On utilise **DB_NTL pour injecter host, user, password, database
        conn = mysql.connector.connect(**DB_NTL)

    except mysql.connector.Error as err:
        raise RuntimeError(f"Connexion MySQL impossible : {err}")

    cur = conn.cursor()

    cur.execute("""
      SELECT Nom, IPv4, OS, OS_Version
        FROM Equipements
        WHERE OS IS NOT NULL
        AND OS_Version IS NOT NULL
    """)

    rows = cur.fetchall()
    conn.close()

    assets = []
    for row in rows:
        hostname, ip, os_name, os_version = row
        assets.append(
            Asset(
                hostname,
                ip,
                os_name,
                os_version
            )
        )

    return assets