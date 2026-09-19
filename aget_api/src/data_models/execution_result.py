from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

class AgentType(str, Enum):
    QUESTION = "QuestionAgent"
    EVALUATION = "EvaluationAgent"
    HINT = "HintAgent"
    EXPLANATION = "ExplanationAgent"
    SUMMARY = "SummaryAgent"

    
class ExecutionResult(BaseModel):

    agent_name : AgentType = Field(description="Name of the Agent that produced the execution result")
    agent_skill : AgentSkill = Field(description="Skill of the Associated Agent that produced the execution result")
    user_input : str = Field(description="User Input")
    success : bool = Field(description="Whether the Agent Call is Successfull or Not.")
    event : Action = Field(description="Event handled by the Agent")
    response : Dict | None = Field(description="Agent Response and reasoning in natural language")
    metadata : Dict | None = Field(description="Detailed Agent Response")
    update_memory : bool = True



# Example : Evaluation Agent Output:
# {
#     "score": 3,
#     "answer_status": "correct",
#     "attempts": 1,
#     "misconceptions": [
#         "Decision Boundary"
#     ]
# }