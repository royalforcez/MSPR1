import mysql.connector
from .models import Asset
from session_manager import DB_NTL

def fetch_assets_from_db():
    """
    Récupère les machines avec leur OS et version depuis la base de données NTL.
    """

    try:
        conn = mysql.connector.connect(**DB_NTL)
    except mysql.connector.Error as err:
        raise RuntimeError(f"Connexion MySQL impossible : {err}")

    cur = conn.cursor()

    cur.execute("""
        SELECT 
            e.nom,
            e.ipv4,
            o.nom_os,
            o.version_os
        FROM tb_equipements e
        LEFT JOIN tb_os o ON e.id_os = o.id
        WHERE e.ipv4 IS NOT NULL
    """)

    rows = cur.fetchall()
    conn.close()

    assets = []

    for row in rows:
        hostname, ip, os_name, os_version = row

        assets.append(
            Asset(
                hostname=hostname,
                ip=ip,
                os_name=os_name if os_name else "UNKNOWN",
                os_version=os_version if os_version else "UNKNOWN"
            )
        )

    return assets