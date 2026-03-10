import csv
from .models import Asset


def read_assets_from_csv(path):

    assets = []

    with open(path, "r") as f:

        reader = csv.DictReader(f)

        for line in reader:

            assets.append(
                Asset(
                    line.get("hostname"),
                    line.get("ip"),
                    line.get("os_name"),
                    line.get("os_version")
                )
            )

    return assets