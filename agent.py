from __future__ import annotations

import os
from typing import Any

from fastapi import Body, FastAPI, HTTPException

from claude_code_provider import find_trayectory_with_claude_code

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
    """Return one complete trajectory for the task.

    This is the current subnet contract for harvester-style miners. The miner
    receives the task once and returns a replayable list of tool calls.
    """
    try:
        result = await find_trayectory_with_claude_code(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "web_agent_id": os.getenv("WEB_AGENT_ID", "autoppia-web-agent-example"),
        "trajectory": result.trajectory,
        "success": result.success,
        "confidence": result.confidence,
        "summary": result.summary,
        "failure_reason": result.failure_reason,
        "model_used": os.getenv("CLAUDE_CODE_MODEL", "sonnet"),
        "cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
    }
