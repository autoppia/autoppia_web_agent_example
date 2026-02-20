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
