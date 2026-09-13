from typing import List, Literal, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class PromptVersioning(BaseModel):
     
    version : int = Field(description="Version number of the prompt")
    name : str = Field(description="Name of the prompt")
    prompt_id : str = Field(description="Prompt ID")
    created_at : datetime = Field(description="Creation Date of the prompt")
    author : str = Field(description="Author of the prompt")
    status : str = Field(description="Status of the prompt. Option: test or prod")
    system_prompt : str = Field(description="System Prompt")
    user_prompt : str = Field(description="User Prompt")
    prompt_hash : str = Field(description="Hash value of the prompt")
    difficulty : str = Field(description="Dfficulty level of question generated using this prompt. Options: easy, medium, hard")
