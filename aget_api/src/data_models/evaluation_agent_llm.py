from typing import List, Dict, Literal
from pydantic import BaseModel, Field
from enum import Enum

#This will be present within the metadata of the EvaluationAgent Response:
class AnswerStatus(str, Enum):
    CORRECT = "correct"
    WRONG = "wrong"
    PARTIALLY_CORRECT = "partially_correct"


class EvaluationAgentLLM(BaseModel):
    overall_score : int = Field(description="Score given by the agent on the user answer", min=0, max=5)
    correctness : AnswerStatus = Field(description="Whether the answer is correct or wrong or partially correct") 
    key_points_covered: list[str]
    key_points_missed: list[str]
    concepts_demonstrated: list[str]
    concepts_missed: list[str]
    misconceptions: list[str]
    feedback: str