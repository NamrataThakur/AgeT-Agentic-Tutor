from typing import List, Dict
from pydantic import BaseModel, Field

class QuestionAgentLLM(BaseModel):
    question_id : str  
    reasoning : str 

