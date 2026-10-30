from typing import List, Dict

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from graph.resume_state import ResumeState
from services.knowledge_service import KnowledgeService
from data_models.knowledge_context import KnowledgeContext
from services.redis_service import RedisService
from data_models.session_memory import InterviewStatus



class KnowledgeServiceNode:
    def __init__(self, knowledge_service : KnowledgeService):
        
        #KnowledgeService acts as MCP Client for KnowledgeMCP. 
        #KnowledgeMCP will handle all MongoDB related requests for question bank fetching and generating.
        self.knowledge_service = knowledge_service

        
    async def execute(self, state : AgentState)-> dict:
        context = await self.knowledge_service.get_question_bank(state=state)
        conversation_context = state["conversation_context"]

        #Note: If the question bank is ready and the interview is going to proceed as normal,
        #  then the redis update with saving the question bank along with the entire conversation context will happen in the memory_update node:
        if context["status"] == InterviewStatus.IN_PROGRESS:

            conversation_context.knowledge_context = KnowledgeContext(topic=context["topic"],
                                                question_bank=context["question_bank"], #Question Bank Loaded
                                                bucket_count=context["bucket_bank"]) #Bucket Details Loaded 
            
            return {
                "conversation_context" : conversation_context
            }

        else:

            #Note: If the question bank is NOT ready and the interview is going to be paused for the generation task to complete,
            #  then the redis update with saving the conversation context already happened in the KnowledgeService:
            # ResumeState is saved in the redis in the Background Worker already in this case:
            resume_state = ResumeState(interview_id=state["interview_id"],
                                       user_id=state["user_id"],
                                       waiting_job_id=context["job_id"],
                                       pause_reason="Question Bank Generation in progress")


            return {
                "resume_state" : resume_state,
                "response" : context["message"],
                "conversation_context" : conversation_context
            }

            