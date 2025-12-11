from pydantic import BaseModel


class Action(BaseModel):
    """
    Placeholder for agent actions. Extend with concrete action schemas (e.g., clicks, inputs).
    """

    class Config:
        extra = "allow"
