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

from data_models.performance_period import PerformancePeriod

class ConceptCapability(BaseModel):

    concept: str
    current_level: Optional[str] = None
    # weak / beginner / intermediate / strong / expert

    current_score: Optional[float] = None
    trend: Optional[str] = None
    # improving / declining / stable / insufficient_data

    historical_weakness: bool = False
    first_assessed_at: Optional[datetime] = None
    last_assessed_at: Optional[datetime] = None
    timeline: Optional[List[PerformancePeriod] | None]