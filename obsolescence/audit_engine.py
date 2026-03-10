from datetime import date, datetime
from .models import AuditResult


def parse_iso_date(d):

    if not d:
        return None

    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_status(eol_from):

    if eol_from is None:
        return "UNKNOWN", None

    today = date.today()

    delta = (eol_from - today).days

    if delta < 0:
        return "EOL", delta

    if delta <= 90:
        return "SOON_EOL", delta

    return "SUPPORTED", delta


def audit_assets(assets, client):

    results = []

    for a in assets:

        try:

            releases = client.list_releases(a.os_name)

            rel = None

            for r in releases:
                if str(r.get("name")) == a.os_version:
                    rel = r

            if not rel:

                results.append(
                    AuditResult(
                        a.hostname,
                        a.ip,
                        a.os_name,
                        a.os_version,
                        None,
                        None,
                        None,
                        None,
                        "UNKNOWN",
                        None,
                        "version inconnue"
                    )
                )

                continue

            eol_date_str = rel.get("eolFrom")

            eol_dt = parse_iso_date(eol_date_str)

            status, days = compute_status(eol_dt)

            results.append(
                AuditResult(
                    a.hostname,
                    a.ip,
                    a.os_name,
                    a.os_version,
                    a.os_name,
                    rel.get("name"),
                    eol_date_str,
                    rel.get("isEol"),
                    status,
                    days,
                    "OK"
                )
            )

        except Exception as e:

            results.append(
                AuditResult(
                    a.hostname,
                    a.ip,
                    a.os_name,
                    a.os_version,
                    None,
                    None,
                    None,
                    None,
                    "UNKNOWN",
                    None,
                    str(e)
                )
            )

    return results