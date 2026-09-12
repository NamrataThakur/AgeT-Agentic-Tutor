from typing import List, Literal, Dict

from pydantic import BaseModel, Field
from enum import Enum


class AnswerGen(BaseModel):

    answer_text : str = Field(description="Answer Text")
    key_points : List[str] = Field(description="Main key points for evaluation")

    
class QuestionGenLLM(BaseModel):

    question : str = Field(description="Question Text")
    reference_answer : AnswerGen
    primary_concept : str = Field(description="Primary concept involved")
    secondary_concepts : List[str] = Field(description="List of secondary concepts")



class QuestionGenAllBatch(BaseModel):
    """A class representing all questions generated using the topic packet with all info across all chunks.

    Args:
        question_batch : (List[Question]) 

    """
    question_gen_batch : List[QuestionGenLLM]