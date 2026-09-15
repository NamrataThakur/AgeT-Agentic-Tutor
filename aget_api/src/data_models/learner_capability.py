from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.concept_capability import ConceptCapability

class LearnerCapabilityMemory(BaseModel):

    user_id: str = Field(default=None, description="Unique ID for the user") #Primary Key
    concepts: Optional[List[ConceptCapability] | None]
    updated_at: Optional[datetime | None] = Field(default=None, description="Date of the last time memory is derived")