"""
Converter from livingghg v3 parameter CSV to v4 enhanced format.

Converts ipcc_params_AN_v2.csv to the new schema with distribution types,
provenance, and verification status.
"""

import csv
from pathlib import Path

from .registry import DistributionType, ParameterValue, VerificationStatus


def convert_v3_csv(input_path: Path, output_path: Path) -> None:
    """
    Convert v3 parameter CSV to v4 enhanced format.
    
    Args:
        input_path: Path to v3 CSV (ipcc_params_AN_v2.csv)
        output_path: Path for output v4 CSV
    """
    params = []

    with open(input_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows with no default value
            if not row.get("default") or not row["default"].strip():
                continue

            # Build key
            key = f"{row['guideline']}.{row['factor']}.{row['disaggregation']}"

            # Parse status
            status_str = row.get("status", "UNVERIFIED").upper()
            try:
                status = VerificationStatus(status_str)
            except ValueError:
                status = VerificationStatus.UNVERIFIED

            # Infer distribution type from presence of lower/upper
            has_range = row.get("lower") and row.get("upper")
            dist = DistributionType.UNIFORM if has_range else DistributionType.FIXED

            param = ParameterValue(
                key=key,
                value=float(row["default"]),
                units=row["units"],
                dist=dist,
                dist_params={
                    "lower": float(row["lower"]),
                    "upper": float(row["upper"]),
                }
                if has_range
                else None,
                source_doi_or_url=row.get("source", ""),
                table=row.get("table", ""),
                equation="",
                page=row.get("page", ""),
                region="all",
                status=status,
                verified_by="",
                verified_date=None,
                notes=row.get("range_basis", ""),
            )

            params.append(param)

    # Write v4 CSV
    fieldnames = [
        "key",
        "value",
        "units",
        "dist",
        "dist_lower",
        "dist_upper",
        "source_doi_or_url",
        "table",
        "equation",
        "page",
        "region",
        "status",
        "verified_by",
        "verified_date",
        "notes",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for param in params:
            row = {
                "key": param.key,
                "value": param.value,
                "units": param.units,
                "dist": param.dist.value,
                "dist_lower": param.dist_params.get("lower", "")
                if param.dist_params
                else "",
                "dist_upper": param.dist_params.get("upper", "")
                if param.dist_params
                else "",
                "source_doi_or_url": param.source_doi_or_url,
                "table": param.table,
                "equation": param.equation,
                "page": param.page,
                "region": param.region,
                "status": param.status.value,
                "verified_by": param.verified_by,
                "verified_date": param.verified_date.isoformat()
                if param.verified_date
                else "",
                "notes": param.notes,
            }
            writer.writerow(row)


if __name__ == "__main__":
    # Convert v3 CSV when run as script
    import sys

    if len(sys.argv) != 3:
        print("Usage: python -m ghgsim.core.converter <input_v3.csv> <output_v4.csv>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    convert_v3_csv(input_path, output_path)
    print(f"Converted {input_path} -> {output_path}")
