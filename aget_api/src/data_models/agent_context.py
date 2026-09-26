#This context will flow to the Specialised Agents like QuestionAgent, AnswerEvaluationAgent etc:
from typing import Dict
from pydantic import BaseModel, Field

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from data_models.a2a_task import A2ATask
from data_models.conversation_context import ConversationContext

class AgentContext(BaseModel):

    task : A2ATask
    conversation_context : ConversationContext
    user_input : str


class QuestionAgentContext(BaseModel):

    session_context : Dict
    episodic_context : Dict
    candidate_questions : Dict
    target_difficulty : str
    reasoning : str
    task : A2ATask


class EvalAgentContext(BaseModel):

    session_context : Dict
    task : A2ATask


class EpisodicContext(BaseModel):
    questions_attempted: int
    questions_correct: int
    questions_incorrect: int
    concepts_discussed: list[str]
    difficulty_progression: list[str]
    important_events: list[dict]
    previous_summary: str | None = None


class ProceduralContext(BaseModel):
    questions_attempted: int


class SummaryAgentContext(BaseModel):
    episodic_context : EpisodicContext
    procedural_context : ProceduralContext | None = None


class HintAgentContext(BaseModel):
    current_question : str
    candidate_answer : str
    attempt_no : int
    evaluation_result : dict
    previous_hints: list[str]
    reference_answer: str
    reference_key_points: list[str]
    primary_concept: str
    secondary_concepts : list[str]
    task : A2ATask


class ExplanationAgentContext(BaseModel):
    current_question: str
    candidate_answer: str | None
    attempt_no: int
    hints_given: list[dict]
    evaluation_result : dict
    reference_answer: str
    reference_key_points: list[str]
    primary_concept: str
    secondary_concepts: list[str]
    task : A2ATask
