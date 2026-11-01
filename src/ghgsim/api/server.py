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
async def list_runs(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    """
    List available runs.
    
    Args:
        limit: Max results (default 50)
        offset: Pagination offset
        
    Returns:
        {"runs": [...], "total": N}
    """
    # Stub: would scan results/ directory for manifests
    return {
        "runs": [],
        "total": 0,
        "message": "Stub implementation - no runs loaded",
    }


@app.get("/api/run/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """
    Get single run results.
    
    Args:
        run_id: Run identifier
        
    Returns:
        Run manifest and summary
        
    Raises:
        HTTPException: If run not found
    """
    # Stub: would load from results/{run_id}/manifest.yaml
    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found (stub)")


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
