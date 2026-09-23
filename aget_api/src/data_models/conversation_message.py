from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


class ConversationMessage(BaseModel):

    role: Literal[ "user","assistant"] = Field(description="Who said this")
    content: str = Field(description="What is being said")
    timestamp: datetime = Field(description="When this has been said")
    turn_id: int = Field(default=1, description="At which turn, did they say this")
    agent: Optional[str | None] = Field(default=None, description="Which specialised assistant said this")