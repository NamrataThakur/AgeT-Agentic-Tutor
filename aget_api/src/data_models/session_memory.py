from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.execution_result import ExecutionResult

class InterviewState(str, Enum):
    WAITING_FOR_ANSWER = "waiting_for_answer"
    READY_FOR_NEXT_ACTION = "ready_for_action"
    INTERVIEW_STARTED = "interview_started"


class InterviewStatus(str, Enum):
    INITIALIZING = "initializing"
    WAITING_FOR_QS_BANK = "waiting_for_qs_bank"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SessionMemory(BaseModel):

    user_id : str = Field(default=None, description="Unique ID for the user")
    interview_id : str | None = Field(default=None, description="Unique Interview ID for a particular session")

    #--- Same as the "topic" present in the AgentState ---:
    current_topic : str | None = Field(default=None, description="Topic used in the current interview state")
    current_qs : str | None = Field(default=None, description="Text of Question Asked") 
    current_qs_metadata : Dict | None = Field(default=None, description="All details of the Question Asked") 
    hints_given : list[dict] | None = Field(default=None, description="Latest user input/answer") 
    turn_count : int | None = Field(default=None, description="Interview Turns")
    difficulty : str | None = Field(default=None, description="Difficulty of the current question asked")
    attempt_no : int | None = Field(default=None, description="Number of attempts at the current question",min=1, max=2)

    #ExecutionResult is stored in Session Memory to access between turns.
    last_execution_result : ExecutionResult | None = Field(default=None, description="Result of the most recently executed specialized agent")

    current_bucket : str | None = Field(default=None, description="Bucket name in which the current question belong")

    #Interview Status is the overall status of the interview across turns:
    interview_status : InterviewStatus | None = Field(default=None, description="Whether the interview is ongoing or completed.")

    #Interview State is handling internal state of the interview as it moves from one agent to another:
    interview_state : InterviewState | None = Field(default=None, description="Current State of Interview")