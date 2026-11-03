"""
Run manifest and archiving for reproducibility.

Every run writes a manifest with git commit, file hashes, parameter values,
and execution details. The run_id is the SHA-256 of the canonical manifest.
Reruns with the same manifest must reproduce outputs bit-identically.
"""

import hashlib
import json
import platform
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class GitInfo:
    """Git repository information."""

    commit_sha: str
    branch: str
    is_dirty: bool
    remote_url: str


@dataclass
class FileHash:
    """File hash with path."""

    path: str
    sha256: str


@dataclass
class RunManifest:
    """
    Complete manifest for a run.
    
    The run_id is the SHA-256 of the canonical JSON representation
    (excluding timestamps and run_id itself).
    """

    run_id: str
    created_at: str
    package_version: str
    git: GitInfo | None
    model_yaml_hash: FileHash | None
    module_hashes: list[FileHash]
    parameter_hashes: list[FileHash]
    data_hashes: list[FileHash]
    fork_settings: dict[str, Any]
    rng_seed: int | None
    platform: str
    python_version: str
    allow_unverified: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, canonical: bool = False) -> str:
        """
        Convert to JSON string.
        
        Args:
            canonical: If True, exclude run_id and timestamps for hashing
        """
        data = self.to_dict()
        if canonical:
            # Exclude fields that shouldn't affect run_id
            data.pop("run_id", None)
            data.pop("created_at", None)
        return json.dumps(data, sort_keys=True, indent=2)

    @staticmethod
    def compute_run_id(manifest_dict: dict[str, Any]) -> str:
        """
        Compute run_id from manifest dictionary.
        
        Args:
            manifest_dict: Manifest as dictionary (without run_id/timestamps)
            
        Returns:
            SHA-256 hex digest
        """
        # Create canonical representation
        canonical = dict(manifest_dict)
        canonical.pop("run_id", None)
        canonical.pop("created_at", None)
        canonical_json = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(canonical_json.encode()).hexdigest()


def get_git_info(repo_path: Path | None = None) -> GitInfo | None:
    """
    Get git repository information.
    
    Args:
        repo_path: Path to repository (None = current directory)
        
    Returns:
        GitInfo or None if not a git repository
    """
    try:
        if repo_path:
            git_args = ["-C", str(repo_path)]
        else:
            git_args = []

        # Get commit SHA
        sha = subprocess.check_output(
            ["git"] + git_args + ["rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()

        # Get branch
        branch = subprocess.check_output(
            ["git"] + git_args + ["rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()

        # Check if dirty
        status = subprocess.check_output(
            ["git"] + git_args + ["status", "--porcelain"],
            stderr=subprocess.DEVNULL,
        ).decode()
        is_dirty = bool(status.strip())

        # Get remote URL
        try:
            remote_url = subprocess.check_output(
                ["git"] + git_args + ["config", "--get", "remote.origin.url"],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
        except subprocess.CalledProcessError:
            remote_url = ""

        return GitInfo(
            commit_sha=sha,
            branch=branch,
            is_dirty=is_dirty,
            remote_url=remote_url,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def hash_file(path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        path: Path to file
        
    Returns:
        Hex digest
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def create_manifest(
    package_version: str,
    model_yaml_path: Path | None = None,
    module_files: list[Path] | None = None,
    parameter_files: list[Path] | None = None,
    data_files: list[Path] | None = None,
    fork_settings: dict[str, Any] | None = None,
    rng_seed: int | None = None,
    allow_unverified: bool = False,
    repo_path: Path | None = None,
) -> RunManifest:
    """
    Create a run manifest.
    
    Args:
        package_version: Package version string
        model_yaml_path: Path to model YAML file
        module_files: List of module source files
        parameter_files: List of parameter CSV files
        data_files: List of data files
        fork_settings: Fork configuration
        rng_seed: Random seed for reproducibility
        allow_unverified: Whether unverified parameters were allowed
        repo_path: Repository path for git info
        
    Returns:
        RunManifest with computed run_id
    """
    # Hash model YAML
    model_yaml_hash = None
    if model_yaml_path and model_yaml_path.exists():
        model_yaml_hash = FileHash(
            path=str(model_yaml_path), sha256=hash_file(model_yaml_path)
        )

    # Hash module files
    module_hashes = []
    if module_files:
        for path in module_files:
            if path.exists():
                module_hashes.append(
                    FileHash(path=str(path), sha256=hash_file(path))
                )

    # Hash parameter files
    parameter_hashes = []
    if parameter_files:
        for path in parameter_files:
            if path.exists():
                parameter_hashes.append(
                    FileHash(path=str(path), sha256=hash_file(path))
                )

    # Hash data files
    data_hashes = []
    if data_files:
        for path in data_files:
            if path.exists():
                data_hashes.append(
                    FileHash(path=str(path), sha256=hash_file(path))
                )

    # Get git info
    git_info = get_git_info(repo_path)

    # Create manifest dict (without run_id yet)
    manifest_dict = {
        "run_id": "",
        "created_at": datetime.now().astimezone().isoformat(),
        "package_version": package_version,
        "git": asdict(git_info) if git_info else None,
        "model_yaml_hash": asdict(model_yaml_hash) if model_yaml_hash else None,
        "module_hashes": [asdict(h) for h in module_hashes],
        "parameter_hashes": [asdict(h) for h in parameter_hashes],
        "data_hashes": [asdict(h) for h in data_hashes],
        "fork_settings": fork_settings or {},
        "rng_seed": rng_seed,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "allow_unverified": allow_unverified,
    }

    # Compute run_id
    run_id = RunManifest.compute_run_id(manifest_dict)
    manifest_dict["run_id"] = run_id

    # Create manifest object
    return RunManifest(**manifest_dict)


def save_manifest(manifest: RunManifest, output_path: Path) -> None:
    """
    Save manifest to JSON file.
    
    Args:
        manifest: RunManifest to save
        output_path: Output file path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(manifest.to_json())


def load_manifest(manifest_path: Path) -> RunManifest:
    """
    Load manifest from JSON file.
    
    Args:
        manifest_path: Path to manifest JSON
        
    Returns:
        RunManifest
    """
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    # Convert nested dicts back to dataclasses
    if data["git"]:
        data["git"] = GitInfo(**data["git"])

    if data["model_yaml_hash"]:
        data["model_yaml_hash"] = FileHash(**data["model_yaml_hash"])

    data["module_hashes"] = [FileHash(**h) for h in data["module_hashes"]]
    data["parameter_hashes"] = [FileHash(**h) for h in data["parameter_hashes"]]
    data["data_hashes"] = [FileHash(**h) for h in data["data_hashes"]]

    return RunManifest(**data)
