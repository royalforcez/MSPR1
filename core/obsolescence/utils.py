import os
from datetime import datetime


# =========================================================
# CONFIGURATION EXPORTS
# =========================================================

# Dossier unique pour tous les exports (conforme cahier des charges)
OUTPUT_DIR = "exports"


# =========================================================
# OUTILS FICHIERS
# =========================================================

def ensure_output_dir():
    """
    Crée le dossier d'exports s'il n'existe pas.

    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Impossible de créer le dossier d'export : {e}")


def now_ts():
    """
    Génère un timestamp pour nommer les fichiers.

    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")