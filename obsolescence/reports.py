import csv
import os
from .utils import ensure_output_dir, now_ts, OUTPUT_DIR


def write_report_csv(results, source="audit"):
    """
    Exporte les résultats d'audit au format CSV.

    Le paramètre source permet de contextualiser le nom du fichier :
    - db   -> audit lancé depuis la base
    - csv  -> audit lancé depuis un fichier CSV
    - audit -> valeur par défaut si rien n'est précisé
    """

    ensure_output_dir()

    path = os.path.join(OUTPUT_DIR, f"report_{source}_{now_ts()}.csv")

    fields = [
        "hostname",
        "ip",
        "os_name",
        "os_version",
        "status",
        "eol_date"
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for r in results:
            writer.writerow({
                "hostname": r.hostname,
                "ip": r.ip,
                "os_name": r.os_name,
                "os_version": r.os_version,
                "status": r.status,
                "eol_date": r.eol_date
            })

    return path