import uuid
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from agents.planner_agent import PlannerAgent
from data_models.execution_plan import ExecutionPlan, Action
from data_models.agent_skills import AgentSkill
from agents.planner_policy import PlannerPolicy


class PlannerNode:
    def __init__(self):
        self.planner_agent = PlannerAgent()
        self.planner_policy = PlannerPolicy()

    async def execute(self, state : AgentState):
        print("Flow Reached Planner")

        session_memory = state["conversation_context"].session_memory

        if state["execution_result"] is None:
            execution_result = state["conversation_context"].session_memory.last_eval_result
        else:
            execution_result = state["execution_result"]

        allowed_skills = await self.planner_policy.get_allowed_skills(session_memory=session_memory, execution_result=execution_result)

        llm_response = await self.planner_agent.invoke(state=state, allowed_skills=allowed_skills)

        #Assign Action types based on Skill Chosen:
        if llm_response.skill in [AgentSkill.GENERATE_HINT, AgentSkill.GENERATE_EXPLANATION]:
            action = Action.GENERATE
        elif llm_response.skill in [AgentSkill.ASK_QUESTION]:
            action = Action.ASK_QUESTION
        else:
            action = Action.EVALUATE

        execution_plan = ExecutionPlan(
                                        plan_id = str(uuid.uuid4()),
                                        skill=llm_response.skill,
                                        action=action,
                                        reasoning=llm_response.reasoning
                                    )
        
        return {
            "execution_plan" : execution_plan
        }