import mysql.connector
from .models import Asset


def fetch_assets_from_db():
    """
    Récupère les machines depuis la base MySQL.
    Si la connexion échoue, une exception propre est renvoyée
    pour être gérée par l'interface curses.
    """

    try:
        conn = mysql.connector.connect(
            host="192.168.1.137",
            user="admin_ntl",
            password="Formation2025",
            database="mspr"
        )

    except mysql.connector.Error as err:
        raise RuntimeError(f"Connexion MySQL impossible : {err}")

    cur = conn.cursor()

    cur.execute("""
        SELECT hostname, ip, os_name, os_version
        FROM assets
        WHERE os_name IS NOT NULL
        AND os_version IS NOT NULL
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