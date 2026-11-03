"""
Parameter registry with provenance tracking.

The registry stores all parameters with their values, sources, verification status,
and uncertainty distributions. Default runs REFUSE non-VERIFIED values unless
explicitly allowed with --allow-unverified.
"""

import csv
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path


class VerificationStatus(Enum):
    """Parameter verification status."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    ASSUMPTION = "ASSUMPTION"


class DistributionType(Enum):
    """Parameter uncertainty distribution types."""

    FIXED = "fixed"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    NORMAL = "normal"
    LOGNORMAL = "lognormal"


@dataclass
class ParameterValue:
    """
    A parameter value with full provenance.
    
    Attributes:
        key: Unique parameter key (guideline.factor.disaggregation)
        value: Default/central value
        units: Units (pint-compatible)
        dist: Distribution type for uncertainty
        dist_params: Distribution parameters (e.g., {"lower": x, "upper": y})
        source_doi_or_url: DOI or URL of source document
        table: Table number/name in source
        equation: Equation number/name in source  
        page: Page number in source
        region: Geographic region (e.g., "us", "ca", "all")
        status: Verification status
        verified_by: Name of person who verified
        verified_date: Date of verification
        notes: Additional notes
    """

    key: str
    value: float
    units: str
    dist: DistributionType = DistributionType.FIXED
    dist_params: dict[str, float] | None = None
    source_doi_or_url: str = ""
    table: str = ""
    equation: str = ""
    page: str = ""
    region: str = "all"
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_by: str = ""
    verified_date: date | None = None
    notes: str = ""


class ParameterRegistry:
    """
    Registry of parameters with provenance and verification gates.
    
    Default behavior: REFUSES non-VERIFIED parameters unless allow_unverified=True.
    """

    def __init__(self, allow_unverified: bool = False):
        """
        Initialize the registry.
        
        Args:
            allow_unverified: If True, allow UNVERIFIED/ASSUMPTION parameters
        """
        self.allow_unverified = allow_unverified
        self._params: dict[str, ParameterValue] = {}
        self._overlays: list[dict[str, ParameterValue]] = []

    def register(self, param: ParameterValue) -> None:
        """Register a parameter."""
        self._params[param.key] = param

    def add_overlay(self, overlay: dict[str, ParameterValue]) -> None:
        """
        Add a parameter overlay (e.g., regional parameter set).
        
        Overlays are searched in reverse order (most recent first).
        
        Args:
            overlay: Dictionary of parameter_key -> ParameterValue
        """
        self._overlays.append(overlay)

    def get(self, key: str, for_sampling: bool = False) -> ParameterValue:
        """
        Get a parameter value.
        
        Args:
            key: Parameter key
            for_sampling: If True, return distribution info for MC/Sobol
            
        Returns:
            ParameterValue
            
        Raises:
            ValueError: If parameter not found or not verified
        """
        # Check overlays first (reverse order)
        for overlay in reversed(self._overlays):
            if key in overlay:
                param = overlay[key]
                self._check_verification(param)
                return param

        # Check base registry
        if key not in self._params:
            raise ValueError(f"Parameter '{key}' not found in registry")

        param = self._params[key]
        self._check_verification(param)
        return param

    def _check_verification(self, param: ParameterValue) -> None:
        """
        Check if parameter is verified.
        
        Raises:
            ValueError: If parameter is not verified and allow_unverified=False
        """
        if not self.allow_unverified and param.status != VerificationStatus.VERIFIED:
            raise ValueError(
                f"Parameter '{param.key}' has status {param.status.value}. "
                f"Use --allow-unverified to proceed (will be recorded in manifest)."
            )

    def get_value(self, key: str) -> float:
        """Get just the central value of a parameter."""
        return self.get(key).value

    def list_unverified(self) -> list[ParameterValue]:
        """Return list of all non-VERIFIED parameters."""
        unverified = []
        for param in self._params.values():
            if param.status != VerificationStatus.VERIFIED:
                unverified.append(param)
        for overlay in self._overlays:
            for param in overlay.values():
                if param.status != VerificationStatus.VERIFIED:
                    unverified.append(param)
        return unverified


def load_parameter_csv(csv_path: Path, allow_unverified: bool = False) -> ParameterRegistry:
    """
    Load parameters from an enhanced CSV file.
    
    Supports both v3 format (guideline, factor, disaggregation columns)
    and v4 format (key column with pre-formatted key).
    
    Args:
        csv_path: Path to CSV file
        allow_unverified: If True, allow UNVERIFIED/ASSUMPTION parameters
        
    Returns:
        ParameterRegistry with loaded parameters
    """
    registry = ParameterRegistry(allow_unverified=allow_unverified)

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Detect format: v4 has 'key' column, v3 has 'guideline'
            if "key" in row:
                # v4 format
                key = row["key"]
                value = float(row["value"])
                dist_lower_col = "dist_lower"
                dist_upper_col = "dist_upper"
            else:
                # v3 format (legacy)
                key = f"{row['guideline']}.{row['factor']}.{row['disaggregation']}"
                value = float(row["default"])
                dist_lower_col = "lower"
                dist_upper_col = "upper"

            # Parse distribution
            dist_str = row.get("dist", "fixed").lower()
            try:
                dist = DistributionType(dist_str)
            except ValueError:
                dist = DistributionType.FIXED

            # Parse distribution parameters
            dist_params = {}
            if dist_lower_col in row and row[dist_lower_col]:
                dist_params["lower"] = float(row[dist_lower_col])
            if dist_upper_col in row and row[dist_upper_col]:
                dist_params["upper"] = float(row[dist_upper_col])

            # Parse verification status
            status_str = row.get("status", "UNVERIFIED").upper()
            try:
                status = VerificationStatus(status_str)
            except ValueError:
                status = VerificationStatus.UNVERIFIED

            # Parse date
            verified_date = None
            if "verified_date" in row and row["verified_date"]:
                try:
                    verified_date = date.fromisoformat(row["verified_date"])
                except ValueError:
                    pass

            param = ParameterValue(
                key=key,
                value=value,
                units=row["units"],
                dist=dist,
                dist_params=dist_params if dist_params else None,
                source_doi_or_url=row.get("source", row.get("source_doi_or_url", "")),
                table=row.get("table", ""),
                equation=row.get("equation", ""),
                page=row.get("page", ""),
                region=row.get("region", "all"),
                status=status,
                verified_by=row.get("verified_by", ""),
                verified_date=verified_date,
                notes=row.get("notes", ""),
            )

            registry.register(param)

    return registry
