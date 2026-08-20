import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from aget_api.src.prompt_manager.question_agent_manager import QuestionAgentPromptManager
from data_models.execution_result import AgentType

class PromptService:
    def __init__(self):
        self.question_manager = QuestionAgentPromptManager()

    def load_prompt(self, agent_name : str):

        if agent_name == AgentType.QUESTION:
            prompt = self.question_manager.get_question_agent_prompt()


        return prompt