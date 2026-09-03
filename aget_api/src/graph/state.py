from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, Literal
from typing_extensions import TypedDict
from dataclasses import dataclass
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.conversation_context import ConversationContext
from data_models.execution_plan import ExecutionPlan
from data_models.execution_result import ExecutionResult

from config.constants import CONVERSATION_EVENT

@dataclass   
class RawInput(BaseModel):
    modality : Literal["text","audio","image"]
    data : str | bytes
    mime_data : str


class AgentState(TypedDict, total = False): 

    #--- IDs to track AgeT use----
    user_id : str
    interview_id : str
    #turn_id : int = Field(default=0, description="Turn Count")

    source : Literal["local", "whatsapp"]

    raw_input : RawInput

    #---- After Input Processing -----:
    user_input : str

    #---- Intent Detector -------------
    topic : Optional[str]
    topic_switched : bool | None = None
    
    #---------Memory Manager -----------
    conversation_context : ConversationContext | None = None

    #---------Planner-------------------
    execution_plan : ExecutionPlan | None = None

    #---------Executor------------------- 
    #This contains the final response also
    execution_result : ExecutionResult | None = None

    response : str #Memory Update Node will populate this field


