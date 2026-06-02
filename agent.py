from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI

app = FastAPI(title="Autoppia Web Agent Template API")


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/act", summary="Template action endpoint")
async def act(payload: dict[str, Any] = Body(...)) -> dict[str, list[dict[str, Any]]]:
    """Template endpoint for miners.

    Expected payload shape (simplified):
    - task_id: str
    - prompt: str
    - url: str
    - snapshot_html: str
    - step_index: int
    - history: list

    This template intentionally contains no agentic logic and always returns
    an empty action list so miners can copy the server contract first.
    """
    _ = payload
    return {"actions": []}


@app.post("/step", summary="Alias for /act")
async def step(payload: dict[str, Any] = Body(...)) -> dict[str, list[dict[str, Any]]]:
    return await act(payload)


@app.post("/find_trayectory", summary="Find a complete task trajectory")
async def find_trayectory(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Template endpoint for harvester-style miners.

    Real miners should replace this placeholder with their own trajectory
    discovery logic. The response shape is the current subnet contract.
    """
    _ = payload
    return {
        "web_agent_id": "autoppia-web-agent-example",
        "trajectory": [],
        "success": False,
        "confidence": 0.0,
        "summary": "Template implementation. Replace with real trajectory discovery.",
        "failure_reason": "No concrete harvester implementation configured.",
        "model_used": None,
        "cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
    }
