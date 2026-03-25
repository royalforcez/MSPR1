from datetime import date, datetime
from .models import AuditResult
import re


# =========================================================
# NORMALISATION DES DONNÉES
# =========================================================

def normalize_os(os_name):
    """
    Transforme le nom d'OS en format compatible avec l'API EOL.
    """
    if not os_name:
        return None

    os_name = os_name.lower()

    if "debian" in os_name:
        return "debian"

    if "windows server" in os_name:
        return "windows-server"

    return None


def normalize_version(version, os_name=None):
    """
    Extrait une version simplifiée pour correspondre aux cycles API.
    """

    if not version:
        return None

    # -------------------------------
    # CAS WINDOWS → extraction année
    # -------------------------------
    if os_name and "windows server" in os_name.lower():
        match = re.search(r"\b(20\d{2})\b", os_name)
        if match:
            return match.group(1)

    # -------------------------------
    # CAS LINUX (ex: 10.3 → 10)
    # -------------------------------
    version = str(version)

    if "." in version:
        return version.split(".")[0]

    return version


# =========================================================
# OUTILS DE GESTION DES DATES
# =========================================================

def parse_iso_date(date_str):
    """
    Convertit une date ISO (YYYY-MM-DD) en objet date Python.
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_status(eol_date):
    """
    Détermine le statut de support d'un OS :
    - EOL
    - SOON_EOL
    - SUPPORTED
    """

    if eol_date is None:
        return "UNKNOWN", None

    today = date.today()
    delta = (eol_date - today).days

    if delta < 0:
        return "EOL", delta

    if delta <= 90:
        return "SOON_EOL", delta

    return "SUPPORTED", delta


# =========================================================
# MOTEUR PRINCIPAL D'AUDIT
# =========================================================

def audit_assets(assets, client):
    """
    Analyse une liste d'assets et retourne leur statut EOL.
    
    - assets : liste d'objets Asset
    - client : instance EOLClient
    """

    results = []

    for asset in assets:

        try:
            # -------------------------------
            # 1. Normalisation du produit
            # -------------------------------
            product = normalize_os(asset.os_name)

            if not product:
                results.append(
                    AuditResult(
                        asset.hostname,
                        asset.ip,
                        asset.os_name,
                        asset.os_version,
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
            # 2. Récupération des versions API
            # -------------------------------
            releases = client.list_releases(product)

            # -------------------------------
            # 3. Normalisation de la version
            # -------------------------------
            normalized_version = normalize_version(asset.os_version, asset.os_name)

            matched_release = None

            for release in releases:
                cycle = str(release.get("cycle") or release.get("name"))

                if cycle == normalized_version:
                    matched_release = release
                    break

            # -------------------------------
            # 4. Version non trouvée
            # -------------------------------
            if not matched_release:
                results.append(
                    AuditResult(
                        asset.hostname,
                        asset.ip,
                        asset.os_name,
                        asset.os_version,
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
            # 5. Récupération de la date EOL
            # -------------------------------
            eol_date_str = (
                matched_release.get("eolFrom")
                or matched_release.get("eol")
                or matched_release.get("eolDate")
            )

            eol_date = parse_iso_date(eol_date_str)

            status, days_remaining = compute_status(eol_date)

            # -------------------------------
            # 6. Résultat final
            # -------------------------------
            results.append(
                AuditResult(
                    asset.hostname,
                    asset.ip,
                    asset.os_name,
                    asset.os_version,
                    product,
                    matched_release.get("cycle"),
                    eol_date_str,
                    matched_release.get("isEol"),
                    status,
                    days_remaining,
                    "OK"
                )
            )

        except Exception as e:
            # Gestion des erreurs par asset (ne bloque pas tout l'audit)
            results.append(
                AuditResult(
                    asset.hostname,
                    asset.ip,
                    asset.os_name,
                    asset.os_version,
                    None,
                    None,
                    None,
                    None,
                    "UNKNOWN",
                    None,
                    f"Erreur : {str(e)}"
                )
            )

    return results