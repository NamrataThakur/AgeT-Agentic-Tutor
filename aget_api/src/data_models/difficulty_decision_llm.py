from typing import List, Literal, Dict

from pydantic import BaseModel, Field
from enum import Enum


class DifficultyDecisionLLM(BaseModel):

    """A class representing target difficulty level given the current interview progression.
    
    Args:
        difficulty_level : str
        reasoning : str 

    """
    difficulty_level : str = Field(description="Target Difficulty Level Inferred")
    reasoning : str = Field(description="Reasoning for the choice")
