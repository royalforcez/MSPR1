from dataclasses import dataclass
from typing import Optional


# Représente une machine à auditer
@dataclass
class Asset:
    hostname: str
    ip: Optional[str]
    os_name: str
    os_version: str


# Représente le résultat de l'audit
@dataclass
class AuditResult:
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