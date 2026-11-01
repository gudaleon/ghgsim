"""
Local dashboard server (FastAPI).

Serves results browser and comparison tools for run manifests.
SECURITY: Localhost-only (127.0.0.1), no external access.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create app with security restrictions
app = FastAPI(
    title="ghgsim Dashboard",
    description="Local results browser (localhost-only)",
    version="0.1.0",
)


class RunManifest(BaseModel):
    """Run manifest model."""
    run_id: str
    timestamp: str
    guideline: str
    n_counties: int
    total_co2e_t: float
    params_file: str


class CompareRequest(BaseModel):
    """Comparison request."""
    run_ids: list[str]
    metric: str = "CO2e_t"


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ghgsim Dashboard API",
        "version": "0.1.0",
        "endpoints": ["/api/runs", "/api/run/{id}", "/api/manifest/{id}", "/api/compare"],
    }


@app.get("/api/runs")
async def list_runs(limit: int = 50, offset: int = 0, results_dir: str = "results") -> dict[str, Any]:
    """
    List available runs by scanning results directory for manifests.
    
    Args:
        limit: Max results (default 50)
        offset: Pagination offset
        results_dir: Results directory path (default: "results")
        
    Returns:
        {"runs": [...], "total": N}
    """
    try:
        from ghgsim.core.manifest import load_manifest
        
        results_path = Path(results_dir)
        if not results_path.exists():
            return {
                "runs": [],
                "total": 0,
                "message": f"Results directory not found: {results_dir}",
            }
        
        # Scan for manifest.yaml files
        manifests = []
        for manifest_path in results_path.glob("*/manifest.yaml"):
            try:
                manifest = load_manifest(manifest_path)
                run_dir = manifest_path.parent
                
                # Load results summary if available
                results_file = run_dir / "results.csv"
                summary = {"n_counties": 0, "total_co2e_t": 0.0}
                if results_file.exists():
                    import pandas as pd
                    df = pd.read_csv(results_file)
                    summary["n_counties"] = len(df)
                    if "CO2e_t" in df.columns:
                        summary["total_co2e_t"] = df["CO2e_t"].sum()
                
                manifests.append({
                    "run_id": manifest.run_id,
                    "created_at": manifest.created_at,
                    "package_version": manifest.package_version,
                    "git_commit": manifest.git.commit_sha if manifest.git else None,
                    "git_branch": manifest.git.branch if manifest.git else None,
                    "is_dirty": manifest.git.is_dirty if manifest.git else None,
                    "n_counties": summary["n_counties"],
                    "total_co2e_t": summary["total_co2e_t"],
                    "rng_seed": manifest.rng_seed,
                    "allow_unverified": manifest.allow_unverified,
                    "manifest_path": str(manifest_path),
                })
            except Exception as e:
                logger.warning(f"Failed to load manifest {manifest_path}: {e}")
                continue
        
        # Sort by created_at (newest first)
        manifests.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Paginate
        total = len(manifests)
        paginated = manifests[offset:offset + limit]
        
        return {
            "runs": paginated,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        return {
            "runs": [],
            "total": 0,
            "error": str(e),
        }


@app.get("/api/run/{run_id}")
async def get_run(run_id: str, results_dir: str = "results") -> dict[str, Any]:
    """
    Get single run results with full details.
    
    Args:
        run_id: Run identifier
        results_dir: Results directory path (default: "results")
        
    Returns:
        Run manifest and summary with county-level results
        
    Raises:
        HTTPException: If run not found
    """
    try:
        from ghgsim.core.manifest import load_manifest
        
        results_path = Path(results_dir)
        manifest_path = results_path / run_id / "manifest.yaml"
        
        if not manifest_path.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Run '{run_id}' not found at {manifest_path}"
            )
        
        manifest = load_manifest(manifest_path)
        run_dir = manifest_path.parent
        
        # Load results if available
        results_file = run_dir / "results.csv"
        results_data = None
        if results_file.exists():
            import pandas as pd
            df = pd.read_csv(results_file)
            results_data = df.to_dict(orient="records")
        
        return {
            "manifest": manifest.to_dict(),
            "results": results_data,
            "run_dir": str(run_dir),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading run {run_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/manifest/{run_id}")
async def get_manifest(run_id: str) -> RunManifest:
    """
    Get run manifest.
    
    Args:
        run_id: Run identifier
        
    Returns:
        Run manifest
    """
    raise HTTPException(status_code=404, detail="Stub implementation")


@app.post("/api/compare")
async def compare_runs(request: CompareRequest) -> dict[str, Any]:
    """
    Compare multiple runs.
    
    Args:
        request: Comparison request with run IDs and metric
        
    Returns:
        Comparison results
    """
    if len(request.run_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 runs required")
    
    # Stub: would load results and compute differences
    return {
        "run_ids": request.run_ids,
        "metric": request.metric,
        "message": "Stub implementation",
        "data": [],
    }


def serve(host: str = "127.0.0.1", port: int = 8000, results_dir: Path | None = None):
    """
    Start dashboard server.
    
    Args:
        host: Host address (MUST be 127.0.0.1 for security)
        port: Port number
        results_dir: Results directory to serve
        
    Raises:
        ValueError: If host is not localhost
    """
    import uvicorn
    
    if host not in ("127.0.0.1", "localhost"):
        raise ValueError(
            f"Security violation: host must be 127.0.0.1 or localhost, got '{host}'\n"
            f"ghgsim dashboard is for local use only and must not be exposed to network."
        )
    
    logger.info(f"Starting dashboard server at http://{host}:{port}")
    logger.info(f"Results directory: {results_dir or 'results/'}")
    logger.warning("⚠️  Dashboard server is STUB implementation - endpoints return mock data")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
