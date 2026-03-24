from dataclasses import dataclass
from typing import Optional


# =========================================================
# MODÈLE : ASSET
# =========================================================

@dataclass
class Asset:
    """
    Représente une machine (asset) à auditer.

    """

    hostname: str
    ip: Optional[str]
    os_name: str
    os_version: str


# =========================================================
# MODÈLE : RÉSULTAT D'AUDIT
# =========================================================

@dataclass
class AuditResult:
    """
    Représente le résultat de l’audit d’obsolescence pour une machine.

    """

    hostname: str
    ip: Optional[str]
    os_name: str
    os_version: str

    eol_product: Optional[str]
    matched_cycle: Optional[str]
    eol_date: Optional[str]
    is_eol: Optional[bool]

    status: str
    days_to_eol: Optional[int]
    notes: str