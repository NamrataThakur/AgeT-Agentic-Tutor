from enum import Enum
from pydantic import BaseModel, Field
from typing import Literal


class ResumeState(BaseModel):
    
    interview_id : str = Field(description="Interview Id of the paused graph")
    user_id : str = Field(default=None, description="Unique ID for the user")
    waiting_job_id : str | None = Field(default = None, description="Job Id for which the interview was paused")
    pause_reason : str | None = Field(default = None, description="Pause reason")

    #Background worker will update the status : When initialised -> WAITING, After job completion -> READY, If there is any error -> FAILED
    status : Literal[ "WAITING", "READY", "CONSUMED", "FAILED"] = Field(default = None, description="Whether there is any paused interview")
    error: str | None = None
