import csv
import os
from .models import Asset


def read_assets_from_csv(path):
    """
    Lit un fichier CSV et retourne une liste d'objets Asset.

    Format attendu :
    hostname,ip,os_name,os_version
    """

    # -----------------------------------------------------
    # 1. Vérification existence fichier
    # -----------------------------------------------------
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    assets = []

    try:
        # -------------------------------------------------
        # 2. Ouverture fichier (UTF-8 pour compatibilité)
        # -------------------------------------------------
        with open(path, "r", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            # -------------------------------------------------
            # 3. Validation des colonnes obligatoires
            # -------------------------------------------------
            required_fields = ["hostname", "ip", "os_name", "os_version"]

            if not reader.fieldnames:
                raise ValueError("CSV vide ou mal formaté")

            missing = [field for field in required_fields if field not in reader.fieldnames]

            if missing:
                raise ValueError(
                    f"Colonnes manquantes dans le CSV : {missing}\n"
                    f"Colonnes attendues : {required_fields}"
                )

            # -------------------------------------------------
            # 4. Lecture des lignes
            # -------------------------------------------------
            for line in reader:

                asset = Asset(
                    hostname=line.get("hostname") or "UNKNOWN",
                    ip=line.get("ip") or None,
                    os_name=line.get("os_name") or "UNKNOWN",
                    os_version=line.get("os_version") or "UNKNOWN"
                )

                assets.append(asset)

    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du CSV : {e}")

    return assets