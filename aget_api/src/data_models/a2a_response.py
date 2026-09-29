from pydantic import BaseModel, Field
from typing import Dict, List
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill
from data_models.execution_result import AgentType
from data_models.execution_plan import Action

class A2AResponse(BaseModel):
    agent_name : AgentType = Field(description="Name of the Agent that produced the execution result")
    agent_skill : AgentSkill =  Field(description="Skill associated with the Agent that produced the execution result")
    success : bool = Field(description="Whether the Agent Call is Successfull or Not.")
    event : Action = Field(description="Event handled by the Agent")
    response : Dict | None = Field(description="Agent Response needed for the next step ")
    metadata : Dict | None = Field(description="Detailed Response to be saved in DB.")