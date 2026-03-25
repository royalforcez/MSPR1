import json
import os
from .utils import ensure_output_dir, now_ts, OUTPUT_DIR


def write_report_json(results, source="audit"):
    """
    Exporte les résultats d'audit au format JSON.

    """

    # -----------------------------------------------------
    # 1. Création du dossier exports si nécessaire
    # -----------------------------------------------------
    ensure_output_dir()

    # -----------------------------------------------------
    # 2. Génération du nom de fichier
    # -----------------------------------------------------
    file_path = os.path.join(OUTPUT_DIR, f"report_{source}_{now_ts()}.json")

    # -----------------------------------------------------
    # 3. Transformation des résultats
    # -----------------------------------------------------
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

    # -----------------------------------------------------
    # 4. Écriture du fichier JSON
    # -----------------------------------------------------
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": now_ts(),
                    "source": source,
                    "results": data
                },
                f,
                indent=4,
                ensure_ascii=False
            )
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'écriture du rapport : {e}")

    return file_path