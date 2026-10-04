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
from data_models.agent_context import EvalAgentContext

class EvalAgentContextBuilder(BaseContextBuilder):
    
    async def build_session_context(self, session_memory, user_input) -> Dict:
        """
        Current snapshot of the active interview session.
        """
        last_qs = session_memory.current_qs #ONLY question text saved here
        last_qs_difficulty_level = session_memory.difficulty
        current_topic =session_memory.current_topic
        turn_count = session_memory.turn_count

        qs_metadata = session_memory.current_qs_metadata
        ref_answer = qs_metadata["answer_text"]
        key_points = qs_metadata["key_points"]
        primary_concept = qs_metadata["primary_concept"]
        secondary_concepts = qs_metadata["secondary_concepts"]

        context = {
                    "last_qs" : last_qs,
                    "current_difficulty" : last_qs_difficulty_level,
                    "user_input" : user_input,
                    "current_topic" : current_topic, #Might not need
                    "turn_count" : turn_count, #Might not need
                    "ref_answer" : ref_answer,
                    "key_points" : key_points,
                    "primary_concept" : primary_concept,
                    "secondary_concepts" : secondary_concepts,


                }
        return context

    async def build_context(self, common_context) -> EvalAgentContext:

        session_memory = common_context.conversation_context.session_memory
        user_input = common_context.user_input
        session_context = await self.build_session_context(session_memory=session_memory, user_input=user_input)
        print("Session Context Built Successfully..!")
        
        task = common_context.task #Check what this payload contains
        
        context = EvalAgentContext(
            session_context=session_context,
            task=task
        )
        print("Context for Evaluation Agent Built Successfully..!")

        return context
