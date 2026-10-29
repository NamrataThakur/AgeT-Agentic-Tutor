import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.memory_service import MemoryService

class MemoryManagerNode:
    def __init__(self, memory_service : MemoryService):
        self.memory_service = memory_service

    async def execute(self, state : AgentState) -> dict:

        context, resume_state = await self.memory_service.get_or_create_services(state=state)

        return {
            "conversation_context" : context,
            "resume_state" : resume_state if resume_state else None
        }