import os
from datetime import datetime

# dossier de sortie
OUTPUT_DIR = os.path.join("outputs", "obsolescence")


def ensure_output_dir():
    """
    Crée le dossier outputs/obsolescence si il n'existe pas
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def now_ts():
    """
    Génère un timestamp pour nommer les rapports
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")