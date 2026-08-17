from datetime import datetime
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.redis_service import RedisService
from services.mongodb_service import MongoDBService
from graph.state import AgentState
from data_models.conversation_context import ConversationContext
from data_models.session_memory import SessionMemory
from data_models.conversation_message import ConversationMessage


class MemoryService:
    def __init__(self):
        self.redis_service = RedisService()
        self.mongo_service = MongoDBService()

    async def get_or_create_services(self, state : AgentState) -> ConversationContext:

        #User ID is used to check the MongoDB that stores episodic and procedural memories:
        user_id = state["user_id"] 

        #Interview ID is used to check Redis that stores session memories:
        interview_id = state["interview_id"]

        #conversation_context = self.redis_service.get_interview(interview_id=interview_id)

        # if conversation_context is not None:
        #     print(f"Conversation Context exists for interview id : {interview_id}")
        #     return conversation_context

        print(f"Conversation Context does NOT exists for interview id : {interview_id}")
        print("Creating Memories..!")

        #Create the Session Memory: Redis Exists:
        #session_memory = SessionMemory(interview_status="interview_started")

        #To Be used only for local testing in the absence of Redis:
        session_memory = await self.mongo_service.get_or_create_session_memory(interview_id=interview_id)

        #Create Episodic Memory:
        episodic_memory = await self.mongo_service.get_or_create_episodic_memory(user_id=user_id, interview_id=interview_id)

        #Create Procedural Memory:
        procedural_memory = await self.mongo_service.get_or_create_procedural_memory(user_id=user_id)

        #Preparing Messages:
        messages = ConversationMessage(
            role="user",
            content=state["user_input"],
            timestamp=datetime.today(),
            turn_id=1,
            agent=None
        )

        print("Memories Created. Building Conversation Context Now..!")


        conversation_context = ConversationContext(
                                    session_memory=session_memory,
                                    episodic_memory=episodic_memory,
                                    procedural_memory=procedural_memory,
                                    knowledge_context=None,
                                    learner_capability_memory=None,
                                    messages=[messages]
                                )

        print(f"Storing the Conversation Context in Redis for interview id : {interview_id}")
        #await self.redis_service.save_interview(interview_id=interview_id, context=conversation_context)
        
        return conversation_context