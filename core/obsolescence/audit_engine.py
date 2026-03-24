from datetime import date, datetime
from .models import AuditResult
import re

# =========================================================
# NORMALISATION
# =========================================================

def normalize_os(os_name):
    if not os_name:
        return None

    os_name = os_name.lower()

    if "debian" in os_name:
        return "debian"

    if "windows server" in os_name:
        return "windows-server"

    return None


def normalize_version(version, os_name=None):
    if not version:
        return None

    # -------------------------------
    # CAS WINDOWS → extraction année depuis Caption
    # -------------------------------
    if os_name and "windows server" in os_name.lower():
        match = re.search(r"\b(20\d{2})\b", os_name)
        if match:
            return match.group(1)

    # -------------------------------
    # CAS LINUX (Debian, etc.)
    # -------------------------------
    version = str(version)

    if "." in version:
        return version.split(".")[0]

    return version


# =========================================================
# OUTILS DATE / STATUT
# =========================================================

def parse_iso_date(d):
    if not d:
        return None

    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_status(eol_from):
    if eol_from is None:
        return "UNKNOWN", None

    today = date.today()
    delta = (eol_from - today).days

    if delta < 0:
        return "EOL", delta

    if delta <= 90:
        return "SOON_EOL", delta

    return "SUPPORTED", delta


# =========================================================
# MOTEUR D'AUDIT
# =========================================================

def audit_assets(assets, client):

    results = []

    for a in assets:

        try:
            # -------------------------------
            # 1. Normalisation OS
            # -------------------------------
            product = normalize_os(a.os_name)

            if not product:
                results.append(
                    AuditResult(
                        a.hostname,
                        a.ip,
                        a.os_name,
                        a.os_version,
                        None,
                        None,
                        None,
                        None,
                        "UNKNOWN",
                        None,
                        "OS non supporté par l'API"
                    )
                )
                continue

            # -------------------------------
            # 2. Appel API
            # -------------------------------
            releases = client.list_releases(product)

            # -------------------------------
            # 3. Normalisation version
            # -------------------------------
            normalized_version = normalize_version(a.os_version, a.os_name)

            rel = None

            for r in releases:
                cycle = str(r.get("cycle") or r.get("name"))

                if cycle == normalized_version:
                    rel = r
                    break

            # -------------------------------
            # 4. Version non trouvée
            # -------------------------------
            if not rel:
                results.append(
                    AuditResult(
                        a.hostname,
                        a.ip,
                        a.os_name,
                        a.os_version,
                        product,
                        None,
                        None,
                        None,
                        "UNKNOWN",
                        None,
                        f"version inconnue ({normalized_version})"
                    )
                )
                continue

            # -------------------------------
            # 5. Récupération EOL
            # -------------------------------
            eol_date_str = (
                rel.get("eolFrom")
                or rel.get("eol")
                or rel.get("eolDate")
            )

            eol_dt = parse_iso_date(eol_date_str)

            status, days = compute_status(eol_dt)

            # -------------------------------
            # 6. Résultat final
            # -------------------------------
            results.append(
                AuditResult(
                    a.hostname,
                    a.ip,
                    a.os_name,
                    a.os_version,
                    product,
                    rel.get("cycle"),
                    eol_date_str,
                    rel.get("isEol"),
                    status,
                    days,
                    "OK"
                )
            )

        except Exception as e:
            results.append(
                AuditResult(
                    a.hostname,
                    a.ip,
                    a.os_name,
                    a.os_version,
                    None,
                    None,
                    None,
                    None,
                    "UNKNOWN",
                    None,
                    str(e)
                )
            )

    return results