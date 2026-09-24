from typing import Dict, Any, List
from typing_extensions import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ConceptPerformance(BaseModel):
    concept: str = Field(description="Technical concept assessed during the interview")

    attempts: int = Field(default=None,description="Number of attempts on this concept")

    correct: int = Field(default=None, description="Number of correct attempts")

    incorrect: int = Field(default=None,description="Number of incorrect attempts")

    accuracy: Optional[float] = Field(default=None, description="Accuracy for this concept during this period")

    difficulty_levels: List[str] = Field(default_factory=list,description="Difficulty levels at which this concept was assessed")

    average_score: Optional[float] = Field(default=None, description="Average evaluation score for this concept")

    trend: Optional[str] = Field(default=None,description="Performance trend: improving, declining, stable")

    assessed_at: Optional[datetime] = Field(default=None,description="Most recent assessment time")