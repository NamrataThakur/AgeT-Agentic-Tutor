import os
import sys
from abc import ABC, abstractmethod

os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from data_models.a2a_task import A2ATask
from data_models.a2a_response import A2AResponse
from data_models.agent_context import AgentContext

class BaseAgent(ABC):
    def __init__(self):
        self.name = str
        self.description = str
        self.skills = str

    @abstractmethod
    def invoke(self, context : AgentContext) -> A2AResponse:

        return



#A2A Agent Card:
# {
#   "name": "EvaluationAgent",

#   "description": "Evaluates interview answers.",

#   "skills": [

#       "evaluate_answer",

#       "difficulty_recommendation"

#   ]
# }