from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill


class Action(str, Enum):
    GENERATE = "generate"
    ASK_QUESTION = "ask_question"
    EVALUATE = "evaluate"

class ExecutionPlan(BaseModel):

    plan_id : str = Field(description="Unique UUID for the current plan")
    skill : AgentSkill = Field(description="Skill required to complete task.")
    action : Action = Field(description="Action associated with the Specialised Agent. ")
    reasoning: str | None = Field(default=None, description="Planner Agent's reasoning to select the skill ")
    inputs : Dict[str, Any]
    metadata : Dict[str, Any]
    terminal : bool = False