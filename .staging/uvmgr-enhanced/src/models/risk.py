"""
Risk Management Models (DSLModel Pattern)
=========================================

Declarative models for dependency risk assessment and management.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilitySource(str, Enum):
    NVD = "nvd"  # National Vulnerability Database
    GHSA = "ghsa"  # GitHub Security Advisory
    OSV = "osv"  # Open Source Vulnerabilities
    PYPA = "pypa"  # Python Packaging Authority


class DependencyRisk(BaseModel):
    """Risk assessment for a single dependency"""

    package_name: str
    current_version: str
    latest_version: str | None = None

    # Vulnerability Information
    vulnerabilities: list["Vulnerability"] = Field(default_factory=list)

    # Maintenance Risk
    last_release_date: datetime | None = None
    days_since_last_release: int | None = None
    is_deprecated: bool = False
    is_yanked: bool = False

    # License Risk
    license: str | None = None
    license_risk: RiskLevel = RiskLevel.LOW

    # Overall Risk
    overall_risk: RiskLevel = RiskLevel.LOW
    risk_score: float = Field(0.0, ge=0.0, le=100.0)


class Vulnerability(BaseModel):
    """Security vulnerability details"""

    id: str  # CVE-YYYY-NNNN or GHSA-xxxx-xxxx-xxxx
    source: VulnerabilitySource
    severity: RiskLevel
    summary: str
    affected_versions: str  # e.g., ">=1.0.0,<1.2.3"
    fixed_version: str | None = None
    published_date: datetime
    references: list[str] = Field(default_factory=list)
