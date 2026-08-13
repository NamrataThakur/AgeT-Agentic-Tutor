from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from data_models.a2a_task import A2ATask
from data_models.a2a_response import A2AResponse


# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class BaseTransport(ABC):
    @abstractmethod
    def dispatch(self, task : A2ATask) -> A2AResponse:
        pass 