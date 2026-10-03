import warnings
import json
import hashlib
import re
from datetime import datetime
from typing import Dict, List

warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from context_builder.base_context_builder import BaseContextBuilder
from data_models.agent_context import ExplanationAgentContext

class ExplanationAgentContextBuilder(BaseContextBuilder):

    async def build_session_context(self, session_memory, user_input) -> Dict:
        """
        Current snapshot of the active interview session.
        """
        last_qs = session_memory.current_qs #ONLY Qs Text is stored here
        reference_answer = session_memory.current_qs_metadata["answer_text"]
        reference_key_points = session_memory.current_qs_metadata["key_points"]
        primary_concept = session_memory.current_qs_metadata["primary_concept"]
        secondary_concepts = session_memory.current_qs_metadata["secondary_concepts"]

        last_execution_result = session_memory.last_execution_result.metadata #Evaluation Agent Entire Output
        attempt_no =session_memory.attempt_no
        hints_given = session_memory.hints_given

        context = {
                    "last_qs" : last_qs,
                    "reference_answer" : reference_answer,
                    "last_execution_result" : last_execution_result,
                    "user_input" : user_input,
                    "attempt_no" : attempt_no,
                    "hints_given" : hints_given,
                    "reference_key_points" : reference_key_points,
                    "secondary_concepts" : secondary_concepts,
                    "primary_concept" : primary_concept
                }
        return context
    
    
    async def build_context(self, common_context) -> ExplanationAgentContext:

        session_memory = common_context.conversation_context.session_memory
        user_input = common_context.user_input
        session_context = await self.build_session_context(session_memory=session_memory, user_input=user_input)
        print("Session Context Built Successfully..!")


        task = common_context.task #Check what this payload contains

        context = ExplanationAgentContext(
            current_question=session_context["last_qs"],
            candidate_answer=session_context["user_input"],
            attempt_no=session_context["attempt_no"],
            task=task,
            evaluation_result=session_context["last_execution_result"],
            previous_hints=session_context["hints_given"],
            reference_answer=session_context["reference_answer"],
            reference_key_points=session_context["reference_key_points"],
            secondary_concepts=session_context["secondary_concepts"],
            primary_concept=session_context["primary_concept"]
        )
        print("Context for Explanation Agent Built Successfully..!")

        return context