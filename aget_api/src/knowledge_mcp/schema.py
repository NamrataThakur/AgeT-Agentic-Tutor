from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class QSBankStatus(str, Enum):
    READY = "ready"
    CREATING = "creating"
    RUNNING = "running"
    FAILED = "failed"
    REGENERATING = "regenerating"

#--- Request and Response format for the GetQsBank tool of Knowledge MCP ---
class GetQSBankRequest(BaseModel):
    topic_id : str = Field(description="The Topic ID for which we are quering MCP for Question Bank")
    user_input : str = Field(description="Processed User Input")
    user_id : str = Field(default=None, description="Unique ID for the user")
    interview_id : str | None = Field(default=None, description="Unique Interview ID for a particular session")


class GetQSBankResponse(BaseModel):
    topic_id : str = Field(description="The Topic ID for which we are quering MCP for Question Bank")
    status : QSBankStatus = Field(description="The status of question bank for the topic id")
    qs_bank : dict[str, Any] | None = Field(default=None, description="The Topic ID for which we are quering MCP for Question Bank")
    message : str | None = Field(default=None, description="The message from the MCP")
    error : str | None = Field(default=None, description="The error message from the MCP")
    job_id : str | None = Field(default=None, description="The id of the background job running internally.")
    eta_in_secs : int | None = Field(default=None, description="Estimated time of completion of the running job")


#--- Request and Response format for the CreateQSBank tool of Knowledge MCP ---
class CreateQSBankRequest(BaseModel):
    topic_id : str = Field(description="The Topic ID for which we are quering MCP for Question Bank")
    user_input : str = Field(description="Processed User Input")

class CreateQSBankResponse(BaseModel):
    topic_id : str = Field(description="The Topic ID for which we are quering MCP for Question Bank")
    status : QSBankStatus = Field(description="The status of question bank for the topic id")
    qs_bank : dict[str, Any] | None = Field(default=None, description="The Topic ID for which we are quering MCP for Question Bank")
    message : str | None = Field(default=None, description="The message from the MCP")
    error : str | None = Field(default=None, description="The error message from the MCP")
    job_id : str | None = Field(default=None, description="The id of the background job running internally.")
    eta_in_secs : int | None = Field(default=None, description="Estimated time of completion of the running job")
