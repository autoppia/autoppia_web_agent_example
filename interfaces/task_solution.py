from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from interfaces.actions import Action


class TaskSolution(BaseModel):
    """
    Mocked representation of a full task solution from the agent.
    Extend when wiring real solver logic.
    """

    status: str = Field(
        ..., description="High-level status for the task (e.g., completed, failed, pending)"
    )
    summary: str = Field(
        ..., description="Short human-readable summary describing what the agent did"
    )
    actions: list[Action] = Field(
        default_factory=list,
        description="Ordered list of actions the agent executed or plans to execute",
    )
    final_answer: Optional[str] = Field(
        default=None,
        description="Optional final answer or output produced by the agent",
    )
