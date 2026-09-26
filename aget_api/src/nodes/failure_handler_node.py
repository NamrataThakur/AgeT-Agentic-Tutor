#Failure Handler Node will clear/invalidate the bakground job related resume state. 
# It will not end the interview. Hence, the conversation context will NOT be cleared. 

import os
import sys
from pathlib import Path
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.failure_recovery_service import FailureRecoveryService


class FailureHandlerNode:
    def __init__(self):
        self.recovery_service = FailureRecoveryService()

    async def execute(self, state: AgentState) -> dict:

        context = self.recovery_service.recover(state=state)
        
        #Step 4. Tell the user what happened    
        return {
            "conversation_context" : context,
            "resume_state" : None,
            "response" : ("Question bank generation failed. "
                            "Your previous question bank is still available. Would you like to continue?")
        }