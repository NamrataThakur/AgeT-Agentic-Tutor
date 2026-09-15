from pydantic import BaseModel, Field
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill

class PlannerResponse(BaseModel):

    skill : AgentSkill = Field(description="Skill required to complete task.")
    reasoning: str  = Field(description="Planner Agent's reasoning to select the skill ")