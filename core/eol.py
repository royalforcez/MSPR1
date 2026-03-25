import mysql.connector
import requests
import re
from datetime import datetime


EOL_API_BASE = "https://endoflife.date/api/v1"


# =====================================================
# NORMALISATION
# =====================================================

def normalize_os(os_name):
    if not os_name:
        return None

    os_name = os_name.lower()

    if "debian" in os_name:
        return "debian"

    if "windows server" in os_name:
        return "windows-server"

    if "ubuntu" in os_name:
        return "ubuntu"

    return None


def normalize_version(version, os_name=None):
    if not version:
        return None

    if os_name and "windows server" in os_name.lower():
        match = re.search(r"\b(20\d{2})\b", os_name)
        if match:
            return match.group(1)

    version = str(version)

    if "." in version:
        return version.split(".")[0]

    return version


# =====================================================
# API EOL
# =====================================================

def get_releases(product):
    url = f"{EOL_API_BASE}/products/{product}"

    r = requests.get(url)

    if r.status_code != 200:
        raise RuntimeError(f"Erreur API pour {product}")

    data = r.json()

    return (data.get("result") or {}).get("releases") or []


# =====================================================
# BDD
# =====================================================

def fetch_os_from_db(db_config):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            e.id_os,
            o.nom_os,
            o.version_os
        FROM tb_equipements e
        JOIN tb_os o ON e.id_os = o.id
        WHERE o.nom_os IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def upsert_eol(conn, id_os, date_exp, fin_support):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM tb_end_of_life WHERE id_os = %s
    """, (id_os,))

    existing = cursor.fetchone()

    now = datetime.now()

    if existing:
        cursor.execute("""
            UPDATE tb_end_of_life
            SET 
                date_expiration = %s,
                fin_support = %s,
                last_update = %s
            WHERE id_os = %s
        """, (date_exp, fin_support, now, id_os))
    else:
        cursor.execute("""
            INSERT INTO tb_end_of_life
            (id_os, date_expiration, fin_support, last_update)
            VALUES (%s, %s, %s, %s)
        """, (id_os, date_exp, fin_support, now))

    conn.commit()


# =====================================================
# MAIN JOB
# =====================================================

def run_eol_feed(db_config):
    """
    Fonction appelée par la tâche automatique
    """

    conn = mysql.connector.connect(**db_config)

    os_list = fetch_os_from_db(db_config)

    for id_os, os_name, os_version in os_list:

        try:
            product = normalize_os(os_name)

            if not product:
                continue

            releases = get_releases(product)

            version = normalize_version(os_version, os_name)

            matched = None

            for r in releases:
                cycle = str(r.get("cycle") or r.get("name"))

                if cycle == version:
                    matched = r
                    break

            if not matched:
                continue

            eol_date = (
                matched.get("eolFrom")
                or matched.get("eol")
                or matched.get("eolDate")
            )

            upsert_eol(conn, id_os, eol_date, eol_date)

        except Exception as e:
            print(f"[EOL ERROR] {os_name} {os_version} -> {e}")

    conn.close()