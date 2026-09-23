#Some of these fields will flow to the "Planner" Node as context. This is persisted in Redis across turns:
from typing import Dict, List
from langchain_core.messages import BaseMessage
from typing_extensions import Optional
from pydantic import BaseModel, Field

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.knowledge_context import KnowledgeContext
from data_models.session_memory import SessionMemory
from data_models.episodic_memory import EpisodicMemory
from data_models.procedural_memory import ProceduralMemory
from data_models.learner_capability import LearnerCapabilityMemory
from data_models.conversation_message import ConversationMessage

class ConversationContext(BaseModel):

    session_memory : SessionMemory | None = Field(default=None, description="Short Term Memory stored in Redis")
    episodic_memory : EpisodicMemory | None = Field(default=None, description="Long Term Episodic Memory stored in MongoDB")
    procedural_memory : ProceduralMemory | None = Field(default=None, description="Long Term Procedural Memory stored in MongoDB")
    learner_capability_memory : LearnerCapabilityMemory | None = Field(default=None, description="Long Term Memory stored in MongoDB having the user's learning trend")
    knowledge_context : Optional[KnowledgeContext] | None = None 
    messages: Optional[List[ConversationMessage] | None] = Field(default=None,description="Stores all user and ai messages")
