from typing import List, Dict

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.knowledge_service import KnowledgeService


class KnowledgeServiceNode:
    def __init__(self):
        
        #KnowledgeService is quering MongoDB now, 
        #Later it will act as MCP Client for KnowledgeMCP. 
        #KnowledgeMCP will handle all MongoDB related requests.
        self.knowledge_service = KnowledgeService() 

        
    async def execute(self, state : AgentState)-> dict:
        context = await self.knowledge_service.get_question_bank(state=state)
        
        return {
            "conversation_context" : context
        }
        