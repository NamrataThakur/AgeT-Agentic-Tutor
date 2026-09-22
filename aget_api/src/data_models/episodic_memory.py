from typing import Dict, Any, List
from typing_extensions import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.concept_performance import ConceptPerformance

class EpisodicMemory(BaseModel):
    # -------------------------
    # Identity
    # -------------------------
    interview_id : str = Field(default=None, description="Unique Interview ID for a particular session") #Composite
    user_id : str = Field(default=None, description="Unique ID for the user") #Composite Key

    # -------------------------
    # Interview lifecycle
    # -------------------------
    started_at : datetime = Field(default=None, description="Date of the first time user interacted with AgeT")
    completed_at : Optional[datetime | None] = Field(default=None, description="Date of the last time user interacted with AgeT")

    # -------------------------
    # Interview statistics
    # -------------------------
    questions_asked_ids : Optional[List[str] | None] = Field(default=None, description="IDs of questions asked in this episode")
    questions_attempted : Optional[int | None] = Field(default=0, description="How many questions user have answered")
    questions_correct : Optional[int | None] = Field(default=0, description="How many questions correctly answered by the user")
    questions_incorrect : Optional[int | None] = Field(default=0, description="How many questions incorrectly answered by the user")

    # -------------------------
    # Concepts
    # -------------------------
    concepts_discussed : Optional[List[str] | None] = Field(default=None, description="How many concepts discussed across all interview sessions")

    #concept_performance: Optional[List[ConceptPerformance] | None] = Field(default=None, description="Performance for concepts assessed during this interview")

    # -------------------------
    # Interview progression
    # -------------------------
    difficulty_progression : Optional[List[str] | None] = Field(default=None, description="Current Difficulty level user most comfortable with")

    # -------------------------
    # Important events
    # -------------------------
    important_events : Optional[List[dict] | None] = Field(default=None, description="Important Events with this user")

    # -------------------------
    # Interview summary
    # -------------------------
    summary : Optional[str | None] = Field(default=None, description="Summary of all the interactions with the user")