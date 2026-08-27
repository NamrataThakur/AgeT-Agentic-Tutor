import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.memory_service import MemoryService

class MemoryUpdateNode:
    def __init__(self):
        self.memory_service = MemoryService()

    async def execute(self, state : AgentState):
        return