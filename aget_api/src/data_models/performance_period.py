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

from data_models.concept_performance import ConceptPerformance


class PerformancePeriod(BaseModel):
    period: str = Field(description="Time period, e.g. 2026-03 or 2026-04")
    concepts: Optional[List[ConceptPerformance] | None]= Field(default=None, description="Concept-level performance during this period")