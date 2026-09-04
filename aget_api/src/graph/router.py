#This file contains all the routing logic for the Langgraph Graph:
from langgraph.types import Command
from typing import Literal
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from data_models.session_memory import InterviewState
from data_models.execution_result import AgentType

def topic_router(state : AgentState) -> Command[Literal["knowledge_service", "planner"]]:
    # It will check if the topic has changed between turns. 
    # If changed, it will called "Knowledge Service". Else it will route to "Planner"
    if state["topic_switched"]:
        return Command(goto="knowledge_service")
    return Command(goto="planner")


def decision_router(state : AgentState):
    # It will check interview_state. 
    # Based on that, it will either route to "Planner" or END
    current_interview_state = state["conversation_context"].session_memory.interview_state

    if current_interview_state == InterviewState.WAITING_FOR_ANSWER:
        return "finish"
    
    elif current_interview_state == InterviewState.READY_FOR_NEXT_ACTION:
        return "continue"

    raise ValueError(f"Unsupported interview state for decision routing: {current_interview_state}")
    
