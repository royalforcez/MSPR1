import json
import os
from .utils import ensure_output_dir, now_ts, OUTPUT_DIR


def write_report_json(results, source="audit"):
    """
    Exporte les résultats d'audit au format JSON.

    - source = db | csv | network
    - fichier horodaté conforme au cahier des charges
    """

    # Création du dossier si nécessaire
    ensure_output_dir()

    # Nom du fichier avec timestamp
    path = os.path.join(OUTPUT_DIR, f"report_{source}_{now_ts()}.json")

    # Transformation des objets en dictionnaires
    data = []

    for r in results:
        data.append({
            "hostname": r.hostname,
            "ip": r.ip,
            "os_name": r.os_name,
            "os_version": r.os_version,
            "status": r.status,
            "eol_date": r.eol_date,
            "days_to_eol": r.days_to_eol,
            "notes": r.notes
        })

    # Écriture JSON
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now_ts(),
            "source": source,
            "results": data
        }, f, indent=4, ensure_ascii=False)

    return path