#This context contains the Question related information loaded from MongoDB.

from typing import Dict, List
from pydantic import BaseModel, Field

class KnowledgeContext(BaseModel):
    topic : str | None = Field(default=None, description="Topic for Qs Bank")
    question_bank : List[Dict] | None = Field(default=None, description="Question Bank on the topic chosen")
    bucket_count : List[Dict] | None = Field(default=None, description="Bucket Information")
