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

from agents.base_agent import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._registry = {}

    def register(self, agent : BaseAgent):
        skill = agent.skills
        self._registry[skill] = agent

    def discover(self, skill: str) -> BaseAgent:
         return self._registry[skill]



#Application Startup:
# EVALUATE_ANSWER = "answer_evaluation"
# GENERATE_HINT = "hint_generation"
# ASK_QUESTION = "question_generation"
# GENERATE_EXPLANATION = "concept_explanation"

# registry = AgentRegistry()

# registry.register(

#     QuestionAgent()

# )

# registry.register(

#     EvaluationAgent()

# )

# registry.register(

#     HintAgent()

# )

# registry.register(

#     ExplanationAgent()

# )

# registry.register(

#     FollowupAgent()

# )

# registry.register(

#     SummaryAgent()

# )


# runtime = AgentRuntime(

#     prompt_manager

# )

# transport = LocalTransport(

#     registry,

#     runtime

# )

# executor = Executor(

#     transport

# )