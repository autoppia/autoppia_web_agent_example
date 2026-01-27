from typing import Any, List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends

# Local imports - make sure these modules exist and are correctly implemented
from autoppia_iwa.src.llms import LLMConfig, LLMFactory
from autoppia_iwa.src.execution.actions.base import BaseAction


# -----------------------------
# Lifespan context manager
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for initializing resources on app startup and cleanup on shutdown.
    Here, we initialize the OpenAI service instance and store it in app.state.
    """
    # Configuration for the LLM (placeholder: replace with dynamic or env-based config if needed)
    config = LLMConfig(model="gpt-5.2")

    # Create the LLM instance (OpenAI) and store it in app state
    app.state.openai_service = LLMFactory.create_llm(
        "openai",
        config,
        api_key="will_be_replaced_on_gateway"
    )

    # Yield control back to FastAPI - app is ready to serve requests
    yield

    # Optional: add cleanup logic if needed (closing connections, freeing resources)


# -----------------------------
# FastAPI application instance
# -----------------------------
app = FastAPI(
    title="Autoppia Web Agent API",
    lifespan=lifespan  # Attach the lifespan context manager
)


# -----------------------------
# Dependency injection
# -----------------------------
def get_openai_service(request: Request) -> Any:
    """
    Dependency function to access the OpenAI service from app state.
    Can be injected into any endpoint using Depends().
    """
    return request.app.state.openai_service


# -----------------------------
# Health check endpoint
# -----------------------------
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint.
    Returns a JSON indicating service status.
    """
    return {"status": "healthy"}


# -----------------------------
# Action endpoint
# -----------------------------
@app.post("/act", response_model=List[BaseAction])
async def act(
    payload: Dict[str, Any],
    openai_service: Any = Depends(get_openai_service),
) -> List[BaseAction]:
    """
    Endpoint to execute an action based on the provided payload.
    
    Args:
        payload: JSON payload from the request body.
        openai_service: Injected LLM service instance.

    Returns:
        List of actions. Currently returns a placeholder action.
    """
    # Currently ignoring input; replace this with real action logic
    _ = payload

    # Placeholder action (replace with real action generation)
    return [
        BaseAction(type="ClickAction", x=0, y=0)
    ]
