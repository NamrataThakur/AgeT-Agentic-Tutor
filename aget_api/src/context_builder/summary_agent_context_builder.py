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
from data_models.agent_context import SummaryAgentContext, EpisodicContext, ProceduralContext
from data_models.conversation_context import ConversationContext
from services.prompt_service import PromptService
from config.settings import settings

class SummaryAgentContextBuilder(BaseContextBuilder):

    async def build_episodic_context(self, episodic_memory, old_summary) -> EpisodicContext:
        """
        Persistent interview history accumulated during the session.
        """
        questions_attempted = episodic_memory.questions_attempted
        concepts_discussed = episodic_memory.concepts_discussed
        difficulty_progression_trend = episodic_memory.difficulty_progression
        questions_incorrect = episodic_memory.questions_incorrect
        questions_correct = episodic_memory.questions_correct
        important_events = episodic_memory.important_events
        previous_summary = old_summary

        context = EpisodicContext(
                    questions_attempted =  questions_attempted, 
                    questions_incorrect = questions_incorrect,
                    questions_correct = questions_correct,
                    previous_summary = previous_summary,
                    important_events = important_events,
                    concepts_discussed = concepts_discussed,
                    difficulty_progression = difficulty_progression_trend
                )
        return context


    async def build_procedural_context(self, procedural_memory) -> ProceduralContext | None :
        """
        Persistent interview history accumulated during the session.
        """
        

        context = ProceduralContext(
                    
                )
        return context

    
    async def build_context(self, common_context : ConversationContext) -> SummaryAgentContext:

        episodic_memory = common_context.episodic_memory
        old_summary = common_context.episodic_memory.summary
        episodic_context = await self.build_episodic_context(episodic_memory=episodic_memory, old_summary=old_summary)
        print("Episodic Context Built Successfully..!")

        procedural_memory = common_context.procedural_memory
        procedural_context = await self.build_procedural_context(procedural_memory=procedural_memory)
        print("Procedural Context Built Successfully..!")

        
        context = SummaryAgentContext(
            episodic_context=episodic_context,
            procedural_context=procedural_context
        )
        print("Context for Sumamry Agent Built For Both Episodic And Procedural Memory Successfully..!")

        return context