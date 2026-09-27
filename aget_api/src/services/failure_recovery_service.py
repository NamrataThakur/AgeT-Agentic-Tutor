import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.redis_service import RedisService
from data_models.session_memory import InterviewStatus, InterviewState
from data_models.conversation_context import ConversationContext

class FailureRecoveryService:
    def __init__(self):
        self.redis_service = RedisService()

    async def recover(self, state : AgentState) -> ConversationContext:

        resume_state = state["resume_state"]
        conversation_context = state["conversation_context"]
        session_memory = conversation_context.session_memory

        #Step  1. Consume/clear the failed background job operation:
        #Delete entire state
        await self.redis_service.clear_resumeState(interview_id=state["interview_id"],
                                                    user_id=state["user_id"])

        #Step 2. Keep the existing interview alive:
        session_memory.interview_status = InterviewStatus.IN_PROGRESS
        session_memory.interview_state = InterviewState.INTERVIEW_STARTED
        conversation_context.session_memory = session_memory

        #Step 3. Persist the recovered interview context
        await self.redis_service.save_interview(user_id=state["user_id"],
                                                interview_id=state["interview_id"],
                                                context=conversation_context)

        return conversation_context