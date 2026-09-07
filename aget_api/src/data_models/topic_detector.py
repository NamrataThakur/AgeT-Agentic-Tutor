from pydantic import BaseModel, Field
from typing_extensions import Optional

class TopicStwichDetection(BaseModel):

    topic : str  = Field(default=None, description="Topic Detected from User Input")
    topic_switched : bool  = Field(default=False, description="Whether the topic has switched between turns")