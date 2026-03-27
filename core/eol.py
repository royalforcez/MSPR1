import requests
import re
from datetime import datetime

from core.database import get_connection


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

    if "ubuntu" in os_name:
        return "ubuntu"

    if "windows server" in os_name:
        return "windows-server"

    return None

def normalize_version(version, os_name=None):
    if not version:
        return None

    version = str(version).strip()

    if os_name:
        os_name = os_name.lower()

        # Windows Server
        if "windows server" in os_name:
            match = re.search(r"\b(20\d{2})\b", os_name)
            if match:
                return match.group(1)

        # Debian
        if "debian" in os_name:
            return version.split(".")[0]

        # Ubuntu
        if "ubuntu" in os_name:
            return version 

    return version


# =====================================================
# API
# =====================================================

def get_releases(product):
    url = f"{EOL_API_BASE}/products/{product}"

    r = requests.get(url)

    if r.status_code != 200:
        raise RuntimeError(f"Erreur API pour {product}")

    data = r.json()

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return (data.get("result") or {}).get("releases") or []

    return []


# =====================================================
# BDD
# =====================================================

def fetch_os_from_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nom_os, version_os
        FROM tb_os
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
# MAIN
# =====================================================

def run_eol_feed():
    conn = get_connection()

    os_list = fetch_os_from_db()

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

                if str(cycle).strip() == str(version).strip():
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

            print(f"[EOL OK] {os_name} {os_version} -> {eol_date}")

        except Exception as e:
            print(f"[EOL ERROR] {os_name} {os_version} -> {e}")

    conn.close()