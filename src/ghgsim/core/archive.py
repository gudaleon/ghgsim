"""
Run archiving and reproducibility.

Bundles run manifest, configs, parameters, and results into
reproducible archive packages.
"""

import hashlib
import shutil
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class RunArchiver:
    """
    Create reproducible archives of GHG runs.
    
    Archives include:
    - manifest.yaml: Run metadata
    - params.csv: Parameter values used
    - config.yaml: Model configuration
    - results.csv: County-level results
    - summary.json: Aggregate statistics
    - provenance.yaml: Data sources and versions
    """

    def __init__(self, run_id: str, output_dir: Path | None = None):
        """
        Initialize archiver.
        
        Args:
            run_id: Unique run identifier
            output_dir: Output directory (default: archives/)
        """
        self.run_id = run_id
        self.output_dir = output_dir or Path("archives")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_archive(
        self,
        manifest: dict[str, Any],
        params_path: Path,
        results_path: Path,
        config_path: Path | None = None,
    ) -> Path:
        """
        Create reproducible archive.
        
        Args:
            manifest: Run manifest dict
            params_path: Path to parameter CSV
            results_path: Path to results CSV
            config_path: Optional model config path
            
        Returns:
            Path to created archive (.tar.gz)
        """
        # Create temp staging directory
        staging = self.output_dir / f".staging_{self.run_id}"
        staging.mkdir(exist_ok=True)
        
        try:
            # Copy files to staging
            shutil.copy(params_path, staging / "params.csv")
            shutil.copy(results_path, staging / "results.csv")
            
            if config_path:
                shutil.copy(config_path, staging / "config.yaml")
            
            # Write manifest
            manifest_path = staging / "manifest.yaml"
            with open(manifest_path, "w", encoding="utf-8") as f:
                yaml.dump(manifest, f, default_flow_style=False, sort_keys=True)
            
            # Compute file hashes
            from ghgsim.core.provenance import run_identity

            provenance = {
                "run_id": self.run_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "run_identity": run_identity(),
                "files": {},
            }
            
            for file_path in staging.iterdir():
                if file_path.is_file():
                    file_hash = self._compute_hash(file_path)
                    provenance["files"][file_path.name] = {
                        "sha256": file_hash,
                        "size_bytes": file_path.stat().st_size,
                    }
            
            # Write provenance
            provenance_path = staging / "provenance.yaml"
            with open(provenance_path, "w", encoding="utf-8") as f:
                yaml.dump(provenance, f, default_flow_style=False, sort_keys=True)
            
            # Create tarball
            archive_path = self.output_dir / f"{self.run_id}.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(staging, arcname=self.run_id)
            
            return archive_path
        
        finally:
            # Clean up staging
            if staging.exists():
                shutil.rmtree(staging)

    def extract_archive(self, archive_path: Path, output_dir: Path) -> dict[str, Any]:
        """
        Extract and verify archive.
        
        Args:
            archive_path: Path to .tar.gz archive
            output_dir: Extraction destination
            
        Returns:
            Manifest dict
            
        Raises:
            ValueError: If hash verification fails
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(output_dir)
        
        # Verify hashes
        run_dir = output_dir / self.run_id
        provenance_path = run_dir / "provenance.yaml"
        
        if provenance_path.exists():
            with open(provenance_path, encoding="utf-8") as f:
                provenance = yaml.safe_load(f)
            
            for filename, file_info in provenance.get("files", {}).items():
                if filename == "provenance.yaml":
                    continue  # Skip self
                
                file_path = run_dir / filename
                actual_hash = self._compute_hash(file_path)
                expected_hash = file_info["sha256"]
                
                if actual_hash != expected_hash:
                    raise ValueError(
                        f"Hash mismatch for {filename}:\n"
                        f"  Expected: {expected_hash}\n"
                        f"  Actual:   {actual_hash}"
                    )
        
        # Load manifest
        manifest_path = run_dir / "manifest.yaml"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        
        return manifest

    def _compute_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


def create_manifest(
    run_id: str,
    guideline: str,
    n_counties: int,
    total_co2e_t: float,
    params_file: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create run manifest.
    
    Args:
        run_id: Unique run identifier
        guideline: "IPCC2006" or "IPCC2019"
        n_counties: Number of counties processed
        total_co2e_t: Total CO2e emissions (tonnes)
        params_file: Parameter file used
        **kwargs: Additional metadata
        
    Returns:
        Manifest dict
    """
    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guideline": guideline,
        "n_counties": n_counties,
        "total_co2e_t": total_co2e_t,
        "params_file": params_file,
        **kwargs,
    }
