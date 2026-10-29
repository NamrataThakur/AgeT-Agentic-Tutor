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
    def __init__(self, memory_service : MemoryService):
        self.memory_service = memory_service

    async def execute(self, state : AgentState) -> dict:
        context = await self.memory_service.save_memories(state=state)
        
        return {
            "conversation_context" : context
        }