#AgentRuntime is responsible for: 
#   injecting prompts, attaching shared tools (LLM, parsers, validators), invoking the agent, validating the result.

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from data_models.agent_context import AgentContext
from data_models.a2a_response import A2AResponse
from services.prompt_service import PromptService
from services.context_service import ContextService
from config.settings import settings
from graph.state import AgentState
from data_models.a2a_task import A2ATask
from agents.base_agent import BaseAgent
from data_models.conversation_context import ConversationContext


#TASKS IN AGENT RUNTIME:
# 1. Resolve/load prompt
# 2. Build a Common Agent Context using State and A2ATask
# 3. Prepare agent execution context
# 4. Invoke specialised agent   
# 5. Validate structured output
# 6. Return validated result 

# EXECUTION CONTEXT FORMATS FOR DIFFERENT SPECIALISED AGENTS:
# QuestionAgent
#     → SessionMemory + candidate_questions + prompt

# EvaluationAgent
#     → SessionMemory + latest_answer + current_question + evaluation_prompt

# ExplanationAgent
#     → SessionMemory + evaluation_result + conversation_context + prompt

class AgentRuntime:
    def __init__(self):
        self.prompt_manager = PromptService()
        self.context_service = ContextService()


    def build_common_context(self, state : AgentState, task : A2ATask) -> AgentContext:

        conversation_context = state["conversation_context"]
        user_input = state["user_input"]

        common_context = AgentContext(
            task=task,
            conversation_context=conversation_context,
            user_input=user_input
        )

        return common_context

    async def execute(self, agent : BaseAgent, 
                      state : AgentState | None = None , 
                      task : A2ATask | None = None,
                      context: ConversationContext | None = None,
                      summary : bool = False) -> A2AResponse:

        if state is None and task is None and context is None:
            raise ValueError("At least one execution input must be provided")

        # Step 1: Resolve/load prompt
        prompt = self.prompt_manager.load_prompt(agent_name=agent.name, 
                                                 status=settings.STATUS,
                                                 summary = summary)

        if state is not None and task is not None:
            # Step 2: Build a Common Agent Context using State and A2ATask
            common_context = self.build_common_context(state=state, task=task)
        else:
            common_context = context

        # Step 3: Prepare Specific Agent's execution context using Context Service:
        execution_context = await self.context_service.load_context(agent_name=agent.name, context=common_context)

        # Step 4: Invoke specialised agent
        result = await agent.invoke(context = execution_context.model_dump(), prompt = prompt)

        # Step 5: Validate structured output
        validated_result = self.validate(result)

        # Step 6: Return validated result 
        return validated_result


    def validate(self, result) -> A2AResponse:

        if isinstance(result, A2AResponse):
            return result
        raise ValueError("Agent Response NOT an A2AResponse object.")
