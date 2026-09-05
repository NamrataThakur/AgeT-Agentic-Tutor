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
from data_models.agent_context import QuestionAgentContext
from agents.difficulty_decision_agent import DifficultyDecisionAgent
from services.prompt_service import PromptService
from config.settings import settings

class QuestionAgentContextBuilder(BaseContextBuilder):

    async def build_episodic_context(self, episodic_memory, question_bank) -> Dict:
        """
        Persistent interview history accumulated during the session.
        """
        qs_asked_ids = episodic_memory.questions_asked_ids
        concepts_discussed = episodic_memory.concepts_discussed
        difficulty_progression_trend = episodic_memory.difficulty_progression

        qs_asked = None
        #Episodic Memory is storing IDs of Historical Qs. We extract the Qs Text from the question bank to build the context:
        if qs_asked_ids is not None:
            qs_asked = [qs["question"]["question"] for qs in question_bank if qs["question_id"] in qs_asked_ids]

        context = {
                    "qs_asked" : qs_asked, 
                    "qs_asked_ids" : qs_asked_ids,
                    "concepts_discussed" : concepts_discussed,
                    "difficulty_progression_trend" : difficulty_progression_trend
                }
        return context

    async def build_session_context(self, session_memory, user_input) -> Dict:
        """
        Current snapshot of the active interview session. In case of first turn, most of these will be null.
        """
        last_qs = session_memory.current_qs #ONLY Qs Text is stored here
        last_qs_difficulty_level = session_memory.difficulty
        last_execution_result = session_memory.last_execution_result.response #Evaluation Agent Output
        current_topic =session_memory.current_topic
        turn_count = session_memory.turn_count

        context = {
                    "last_qs" : last_qs,
                    "current_difficulty" : last_qs_difficulty_level,
                    "last_execution_result" : last_execution_result,
                    "user_input" : user_input,
                    "current_topic" : current_topic,
                    "turn_count" : turn_count
                }
        return context
    
    async def build_candidate_questions(self, session_context, episodic_context, question_bank, target_difficulty) -> List[Dict]:

        current_topic = session_context["current_topic"]
        qs_asked_ids = episodic_context["qs_asked_ids"] 

        candidate_questions = []

        for qs in question_bank:
            if qs["question_id"] not in qs_asked_ids and qs["difficulty"] == target_difficulty and qs["topic"] == current_topic:
                candidate_questions.append(
                                            {
                                                "question_id" : qs["question_id"],
                                                "question" : qs["question"]["question"],
                                                "difficulty" : qs["difficulty"],
                                                "bucket_name" : qs["bucket_name"],
                                                "primary_concept" : qs["question"]["primary_concept"],
                                                "secondary_concepts" : qs["question"]["secondary_concepts"],
                                                "answer_text" : qs["question"]["reference_answer"]["answer_text"],
                                                "key_points" : qs["question"]["reference_answer"]["key_points"]
                                            }
                                        )

        return candidate_questions

    async def decide_target_difficulty(self, prompt_service, context) -> tuple[str, str]:

        #If this is the first time the user is interviewing with AgeT (i.e no session memory), assign "easy" as difficulty level:
        if context[0].turn_count == 1:
            target_diff = "easy"
            reasoning = "Interview Starts with Easy Level"

        #If the user is in the process of interviewing with AgeT, let LLM decide/infer the appropiate next difficulty level:
        else:   
            prompt = prompt_service.load_prompt(agent_name="difficulty_decision", status = settings.STATUS)
            agent = DifficultyDecisionAgent()
            target_diff, reasoning = await agent.invoke(prompt=prompt, context=context)

        return target_diff, reasoning

    
    async def build_context(self, common_context) -> QuestionAgentContext:

        session_memory = common_context.conversation_context.session_memory
        user_input = common_context.user_input
        session_context = await self.build_session_context(session_memory=session_memory, user_input=user_input)
        print("Session Context Built Successfully..!")

        episodic_memory = common_context.conversation_context.episodic_memory
        question_bank = common_context.conversation_context.knowledge_context.question_bank
        episodic_context = await self.build_episodic_context(episodic_memory=episodic_memory, question_bank=question_bank)
        print("Episodic Context Built Successfully..!")

        target_difficulty, reasoning = await self.decide_target_difficulty(prompt_service=PromptService(), 
                                                                context=[session_context, episodic_context])
        print("Target Difficulty Inferred Successfully..!")

        
        candidate_questions = await self.build_candidate_questions(session_context=session_context, 
                                                                   episodic_context=episodic_context,
                                                                   question_bank=question_bank,
                                                                   target_difficulty=target_difficulty)
        print("Candidate Questions Selected Successfully..!")

        task = common_context.task #Check what this payload contains

        context = QuestionAgentContext(
            session_context=session_context,
            episodic_context=episodic_context,
            candidate_questions=candidate_questions,
            task=task,
            target_difficulty=target_difficulty,
            reasoning=reasoning
        )
        print("Context for Question Agent Built Successfully..!")

        return context