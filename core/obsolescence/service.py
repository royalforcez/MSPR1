from .audit_db import fetch_assets_from_db
from .audit_csv import read_assets_from_csv
from .audit_engine import audit_assets
from .eol_api import EOLClient
from .reports import write_report_json


def get_eol_client():
    """
    Retourne une instance du client API EOL.

    Cette fonction évite de dupliquer l'initialisation du client
    dans plusieurs endroits du projet.
    """
    return EOLClient()


def list_os_releases(product, client=None):
    """
    Retourne la liste des releases connues pour un produit donné.

    Exemple de produit :
    - ubuntu
    - debian
    - windows-server
    """

    if client is None:
        client = get_eol_client()

    return client.list_releases(product)


def run_audit_from_db(db_config, client=None):
    """
    Lance un audit d'obsolescence à partir des équipements présents
    en base de données.

    - db_config : configuration MySQL
    - client : instance facultative de EOLClient
    """

    if client is None:
        client = get_eol_client()

    assets = fetch_assets_from_db(db_config)
    results = audit_assets(assets, client)

    return results


def run_audit_from_csv(csv_path, client=None):
    """
    Lance un audit d'obsolescence à partir d'un fichier CSV.

    - csv_path : chemin vers le fichier CSV
    - client : instance facultative de EOLClient
    """

    if client is None:
        client = get_eol_client()

    assets = read_assets_from_csv(csv_path)
    results = audit_assets(assets, client)

    return results


def export_audit_results(results, source):
    """
    Exporte les résultats d'audit au format JSON horodaté.

    - results : liste de AuditResult
    - source : db | csv | network
    """

    return write_report_json(results, source=source)