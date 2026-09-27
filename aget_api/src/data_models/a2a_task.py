from pydantic import BaseModel, Field
from typing import Dict, List, Any

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

class A2ATask(BaseModel):
    sender : str
    skill : AgentSkill = Field(description="Skill of the Associated Agent that produced the execution result")
    action : Action
    payload : Dict[str, Any] = Field(description="inputs field of Execution Plan")

    
