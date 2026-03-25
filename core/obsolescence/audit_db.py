import mysql.connector
from .models import Asset


def fetch_assets_from_db(db_config):
    """
    Récupère les machines avec leur OS et version depuis la base de données.

    - db_config : dictionnaire de connexion MySQL
    """

    try:
        conn = mysql.connector.connect(**db_config)
    except mysql.connector.Error as err:
        raise RuntimeError(f"Connexion MySQL impossible : {err}")

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                e.nom,
                e.ipv4,
                o.nom_os,
                o.version_os
            FROM tb_equipements e
            LEFT JOIN tb_os o ON e.id_os = o.id
            WHERE e.ipv4 IS NOT NULL
        """)

        rows = cursor.fetchall()

    finally:
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