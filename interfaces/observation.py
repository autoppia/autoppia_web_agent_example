from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, HttpUrl

from interfaces.actions import Action


class Screenshot(BaseModel):
    media_type: str = Field(default="image/png", description="Screenshot MIME type")
    data: str = Field(..., description="Base64-encoded screenshot image content")


class Observation(BaseModel):
    html_dom: str = Field(..., description="Raw HTML DOM snapshot of the current page")
    screenshot: Screenshot = Field(..., description="Visual snapshot of the page")
    task_prompt: str = Field(..., description="High-level task instruction driving the agent")
    previous_actions: List[Action] = Field(
        default_factory=list,
        description="Ordered history of actions already taken for this task",
    )
    url: HttpUrl = Field(..., description="Current page URL at the time of observation")
