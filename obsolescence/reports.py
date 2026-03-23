import json
import csv
import os
from dataclasses import asdict
from .utils import ensure_output_dir, now_ts, OUTPUT_DIR


def write_report_json(results, source="unknown"):

    ensure_output_dir()

    path = os.path.join(
        OUTPUT_DIR,
        f"report_{source}_{now_ts()}.json"
    )

    payload = {
        "source": source,
        "count": len(results),
        "results": [asdict(r) for r in results]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return path


def write_report_csv(results, source="unknown"):

    ensure_output_dir()

    path = os.path.join(
        OUTPUT_DIR,
        f"report_{source}_{now_ts()}.csv"
    )

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