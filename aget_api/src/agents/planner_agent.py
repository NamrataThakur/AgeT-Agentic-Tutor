from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv

load_dotenv()

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from config.settings import settings
from data_models.execution_plan import ExecutionPlan
from data_models.execution_result import ExecutionResult
from data_models.agent_skills import AgentSkill
from data_models.planner_llm import PlannerResponse
from prompts.planner_node_prompt import PLANNER_NODE_SYSTEM_PROMPT, PLANNER_NODE_USER_PROMPT

openai_api_key = os.getenv("OPENAI_API_KEY")

class PlannerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, #Planner requires stronger model
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)
        

    async def invoke(self, state : AgentState, allowed_skills : list[AgentSkill]):

        attempt_no = state["conversation_context"].session_memory.attempt_no
        previous_hints = state["conversation_context"].session_memory.hints_given
        self.retry_reason = ""

        execution_result = state["execution_result"]
        if execution_result is not None:
            execution_result = execution_result
            last_execution_result = execution_result.model_dump_json(indent=2)
        else:
            execution_result = state["conversation_context"].session_memory.last_execution_result
            last_execution_result = execution_result.model_dump_json(indent=2)

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", PLANNER_NODE_SYSTEM_PROMPT),
                                                        ("user", PLANNER_NODE_USER_PROMPT)
                                                    ]
                                                )
        structured_llm = self.llm.with_structured_output(PlannerResponse)

        planner_chain = prompt | structured_llm

        last_agent_skill = execution_result.agent_skill

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                
                llm_plan = await planner_chain.ainvoke(
                                                        {
                                                            "interview_state": state["conversation_context"].session_memory.interview_state,
                                                            "previous_hints":  previous_hints,
                                                            "last_execution_result" : last_execution_result,
                                                            "user_input" : state["user_input"],
                                                            "allowed_skills" : allowed_skills,
                                                            "attempt_no": attempt_no,
                                                            "max_attempt_no": settings.MAX_ATTEMPTS,
                                                            "retry_reason" : self.retry_reason 
                                                        }
                                                    )
                # --------------------------------------------------
                # Deterministic Planner Validation
                # --------------------------------------------------

                if llm_plan.skill == AgentSkill.GENERATE_HINT:

                    if attempt_no >= settings.MAX_ATTEMPTS:
                        raise ValueError("PLANNER VALIDATION ERROR:"
                                        f"The maximum allowed attempt count has been reached."
                                        f"The Hint Agent is no longer eligible."
                                        f"Select another eligible skill.") 
                    
                    if last_agent_skill == AgentSkill.GENERATE_EXPLANATION:
                        raise ValueError("PLANNER VALIDATION ERROR:"
                                        f"The Explanation Agent has already been called for the current question."
                                        f"The Hint Agent is therefore no longer eligible."
                                        f"Select another eligible skill.")
                    
                print("Plan Created Successfully Using LLM ...!")

                return llm_plan

            except ValueError as exc:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Planner validation failed : {str(exc)}")
                self.retry_reason = str(exc)

                if attempt == settings.MAX_RETRIES:
                    raise

                await asyncio.sleep(2 ** attempt)



# Interview State:
# READY_FOR_NEXT_ACTION

# Session Memory:
# - Topic: Logistic Regression
# - Current difficulty: Medium
# - Attempt: 1
# - Last answer: Incorrect

# Execution Result:
# The user incorrectly explained the sigmoid function.

# Available Skills:

# - give_hint
# - explain_concept

# Choose exactly ONE skill.

    