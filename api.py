from typing import Any, Dict, List, Optional

import os
from functools import lru_cache

from fastapi import FastAPI, Body, HTTPException

from interfaces.actions import Action
from interfaces.observation import Observation
from interfaces.task_solution import TaskSolution

try:
    # Optional dependency: used when OPENAI_API_KEY is configured.
    from autoppia_iwa.src.llms.interfaces import LLMConfig
    from autoppia_iwa.src.llms.service import OpenAIService
except Exception:  # noqa: BLE001
    LLMConfig = None  # type: ignore[assignment]
    OpenAIService = None  # type: ignore[assignment]


FIXED_AUTBOOKS_URL = "http://84.247.180.192:8001/books/book-original-002?seed=36"

app = FastAPI(title="Autoppia Web Agent API")


@lru_cache()
def _get_openai_llm() -> Optional["OpenAIService"]:  # type: ignore[name-defined]
    """
    Lazily construct an OpenAI LLM client using the IWA helper.

    This will only be available when:
      - autoppia_iwa is installed in the environment, and
      - OPENAI_API_KEY is provided.

    The OpenAI Python SDK will pick up HTTPS proxy settings from the
    environment (HTTPS_PROXY) when needed.
    """
    if OpenAIService is None or LLMConfig is None:  # type: ignore[truthy-function]
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "512"))

    cfg = LLMConfig(model=model, temperature=temperature, max_tokens=max_tokens)  # type: ignore[call-arg]
    return OpenAIService(cfg, api_key=api_key)  # type: ignore[arg-type]


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


@app.post("/solve_task_llm", response_model=TaskSolution, summary="Solve a task using OpenAI via IWA LLM")
async def solve_task_llm(payload: Dict[str, Any] = Body(...)) -> TaskSolution:
    """
    Task handler that uses the IWA OpenAIService helper when available.

    This is intended to demonstrate:
      - How miners can plug in the shared LLM layer from autoppia_iwa.
      - How the sandbox proxy can be used to reach the ChatGPT API.
    """
    normalized = _normalize_request(payload)
    observation = Observation(**normalized)

    llm = _get_openai_llm()
    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="OpenAI LLM not configured; ensure autoppia_iwa is installed and OPENAI_API_KEY is set.",
        )

    system_prompt = (
        "You are a concise web task assistant. "
        "Given the current page URL and a user task prompt, "
        "respond with a short final answer describing how the task should be solved."
    )
    user_prompt = (
        f"Current URL: {observation.url}\n\n"
        f"Task: {observation.task_prompt}\n\n"
        "Provide a single-paragraph final answer."
    )
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Use the async OpenAI helper from autoppia_iwa.
    try:
        final_answer = await llm.async_predict(messages)  # type: ignore[call-arg]
    except Exception as e:  # noqa: BLE001
        # Surface the underlying error so it's easier to debug from tests.
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {e}") from e

    actions: List[Action] = [
        {"action_type": "navigate", "url": str(observation.url)},
    ]
    return TaskSolution(
        status="completed",
        summary=f"LLM-based agent produced an answer for {observation.url}",
        actions=actions,
        final_answer=final_answer,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
