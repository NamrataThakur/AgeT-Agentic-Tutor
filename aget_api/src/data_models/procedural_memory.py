from typing import Dict, Any, List
from pydantic import BaseModel, Field
from typing_extensions import Optional
from datetime import datetime

class ProceduralMemory(BaseModel):
    
    user_id : str = Field(default=None, description="Unique ID for the user")
    started_at : datetime = Field(default=None, description="Date of the first time user interacted with AgeT")
    completed_at : Optional[datetime | None] = Field(default=None, description="Date of the last time user interacted with AgeT")
    preferred_difficulty : Optional[str | None] = Field(default=None, description="Difficulty user most comfortable with")
    preferred_questioning_style : Optional[str | None] = Field(default=None, description="User's preferred style for interview")
    preferred_explanation_style : Optional[str | None] = Field(default=None, description="User's preferred explanation style for interview")
    hint_behavior : Optional[str | None] = Field(default=None, description="How the user likes to be given hint")
    recurring_weaknesses : Optional[List[str] | None] = Field(default=None, description="Recurrent concepts user gets wrong")
    recurring_strengths : Optional[List[str] | None] = Field(default=None, description="Recurrent concepts user gets correct")
    learned_interaction_strategies : Optional[str | None] = Field(default=None, description="Strategy to interview the user")