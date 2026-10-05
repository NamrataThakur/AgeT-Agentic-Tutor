from abc import ABC, abstractmethod
from typing import Any
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from context_builder.base_context_builder import BaseContextBuilder

class ContextBuilderRegistry:
    """
    Registry that maps an agent name to its context builder.

    The registry is responsible only for registration and resolution.
    It does not build contexts itself.
    """
    def __init__(self):
        self.builders_registry : dict[str, BaseContextBuilder] = {}

    def register(self, agent_name : str, builder : BaseContextBuilder) -> None:

        if agent_name in self.builders_registry:
            raise ValueError(f"Context builder already registered for agent: {agent_name}")
        
        self.builders_registry[agent_name] = builder

    def get_builder(self, agent_name: str) -> BaseContextBuilder:

        try:
            return self.builders_registry[agent_name]
        except Exception as e:
            raise ValueError(f"No context builder registered for agent: {agent_name}")


    def has_builder(self, agent_name : str) -> bool:
        return agent_name in self.builders_registry