from typing import List, Literal, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Answer(BaseModel):

    answer_text : str = Field(description="Answer Text")
    key_points : List[str] = Field(description="Main key points for evaluation")


class QuestionGen(BaseModel):

    question : str = Field(description="Question Text")
    reference_answer : Answer
    primary_concept : str = Field(description="Primary concept involved")
    secondary_concepts : Optional[List[str]] = Field(description="List of secondary concepts")


class Question(BaseModel):

    topic : str = Field(description="Main Topic the question belongs to")
    knowledge_hash : str = Field(description="Hash value of the main corpus used to generate this question")
    prompt_hash : str = Field(description="Hash Value of the prompt used to generate this question")
    prompt_version : int = Field(description="Version Number of the prompt")
    prompt_id : str = Field("Human Readable version of the prompt used")

    question_id : str = Field(description="Unique ID")
    question : QuestionGen

    difficulty : str = Field(description="Difficulty level of the question. Options: 'easy', 'medium' or 'hard' ")
    bucket_name: Optional[str] = None
    generator_version: str = Field(description="LLM used to generate this question")
    created_at : datetime = Field(description="Date of creation")
    usage : dict 

    semantic_neighbours : List = Field(description="Question IDs neighbours to this question.")


class QuestionAllBatch(BaseModel):
    """A class representing all questions generated using the topic packet with all info across all chunks.

    Args:
        question_batch : (List[Question]) 

    """
    question_batch : List[Question]
