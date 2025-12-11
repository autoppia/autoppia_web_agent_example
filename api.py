from typing import Any, Dict

from fastapi import FastAPI, Body

from interfaces.actions import Action
from interfaces.observation import Observation
from interfaces.task_solution import TaskSolution


FIXED_AUTBOOKS_URL = "http://84.247.180.192:8001/books/book-original-002?seed=36"

app = FastAPI(title="Autoppia Web Agent API")


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/act", response_model=list[Action], summary="Decide next agent actions")
async def act(payload: Dict[str, Any] = Body(...)) -> list[Action]:
    """
    Fixed Autobooks-style CUA endpoint.

    Ignores the incoming observation/state and always returns a single
    navigate action to the known Autobooks BOOK_DETAIL page.

    This matches the behavior of FixedAutobooksAgent and is ideal as a
    simple test agent for the subnet + sandbox pipeline.
    """
    _ = payload  # input is intentionally ignored
    return [
        {"action_type": "navigate", "url": FIXED_AUTBOOKS_URL},
    ]


def _normalize_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept both Observation-style and validator TaskSynapse-style payloads and
    normalize to Observation fields.
    """
    if "html_dom" in payload:
        return payload
    return {
        "html_dom": payload.get("html", "<html></html>"),
        "screenshot": {"media_type": "image/png", "data": payload.get("screenshot", "")},
        "task_prompt": payload.get("prompt", ""),
        "previous_actions": payload.get("previous_actions", []),
        "url": payload.get("url", "http://localhost"),
    }


@app.post("/solve_task", response_model=TaskSolution, summary="Solve a full task")
async def solve_task(payload: Dict[str, Any] = Body(...)) -> TaskSolution:
    """
    Minimal end-to-end task handler.
    Accepts either Observation shape or validator TaskSynapse-like shape.
    """
    normalized = _normalize_request(payload)
    observation = Observation(**normalized)
    actions = [
        {"action_type": "navigate", "url": str(observation.url)},
        {"action_type": "screenshot"},
    ]
    return TaskSolution(
        status="completed",
        summary=f"Stub agent navigated to {observation.url} and captured a screenshot for prompt: {observation.task_prompt}",
        actions=actions,
        final_answer="Completed with stub agent.",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
