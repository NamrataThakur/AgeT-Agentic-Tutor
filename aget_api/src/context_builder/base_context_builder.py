from abc import ABC, abstractmethod
from typing import Any
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_context import AgentContext


class BaseContextBuilder(ABC):
    """Base interface for all agent-specific context builders."""

    @abstractmethod
    async def build_context(self, common_context : AgentContext) -> Any:
        """
        Build the execution context required by a specialised agent.
        """
        raise NotImplementedError