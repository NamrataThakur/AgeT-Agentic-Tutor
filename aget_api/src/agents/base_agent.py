import os
import sys
from abc import ABC, abstractmethod

os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.a2a_response import A2AResponse
from data_models.agent_context import AgentContext
from data_models.agent_skills import AgentSkill
from data_models.execution_result import AgentType

class BaseAgent(ABC):
    def __init__(self):
        self.name = AgentType
        self.description = str
        self.skills = [AgentSkill]
        self.action = str

    @abstractmethod
    async def invoke(self, context : dict, prompt : str) -> A2AResponse:

        return



#A2A Agent Card:
# {
#   "name": "EvaluationAgent",

#   "description": "Evaluates interview answers.",

#   "skills": [
#       "evaluate_answer",

#       "difficulty_recommendation"
#   ],

#   "action" : "generate"

# }