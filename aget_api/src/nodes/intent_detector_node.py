from langgraph.types import Command
from langgraph.graph import END
from typing import Literal
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from agents.intent_detector_agent import IntentDetectionAgent
from tools.topic_detection import TopicDetection
from data_models.session_memory import SessionMemory, InterviewState
from data_models.conversation_context import ConversationContext
from services.mongodb_service import MongoDBService

class IntentDetectorNode:
    def __init__(self):
        self.intent_detector_agent = IntentDetectionAgent()
        self.topic_detector = TopicDetection()

        #To Be used only for local testing in the absence of Redis:
        self.mongo_service = MongoDBService()

    async def execute(self, state : AgentState)-> Command[Literal["topic_router", "__end__"]]:

        conversation_context = state.get("conversation_context")
        current_topic = conversation_context.session_memory.current_topic
        user_input = state.get("user_input")

        if current_topic is None:
            print("No Topic Existing..!")

            print("Query Detected : " , user_input)
            topic_obj, message = self.topic_detector.get_topic(query=user_input)

            if message == "Topic NOT Found in Knowledge Base..!":
                return Command(update={
                                "topic" : topic_obj,
                                "response" : f"{message} Available Topics: {topic_obj}",
                                "topic_switched" : True
                                },
                                goto=END)

            else:
                topic = topic_obj[0].id
                print("Topic Detected : ", topic)
                session_memory = SessionMemory(current_topic=topic,
                                               interview_state=InterviewState.INTERVIEW_STARTED) #interview state going as null in mongodb --> fix it
                print(session_memory)
    
                #To Be used only for local testing in the absence of Redis:
                await self.mongo_service.update_session_memory(interview_id=state["interview_id"], 
                                                            memory=session_memory)
    
                #To be used for Prod testing in the presence of Redis:
                conversation_context.session_memory = session_memory
                return Command(update={
                                "topic" : topic,
                                "response" : message,
                                "topic_switched" : True,
                                "conversation_context" : conversation_context
                                },
                                goto="topic_router")
            
        else:
            print("Topic Existing. Checking Current Topic from user input..!")
            print("Current Topic : ", current_topic)

            # session_memory = conversation_context.session_memory
            response = await self.intent_detector_agent.invoke(state=state)

            #We need the topic id to remain consistent with the names present in the MongoDB, so that QS Bank can be fetched/generated. 
            #So parsing the LLM response with deterministic topic detector.
            topic_obj, message = self.topic_detector.get_topic(query=response.topic)

            if message == "Topic NOT Found in Knowledge Base..!":
                return Command(update={
                                "topic" : topic_obj,
                                "response" : f"{message} Available Topics: {topic_obj}",
                                "topic_switched" : response.topic_switched
                                },
                                goto=END)
            
            else:
                topic = topic_obj[0].id
                print("Topic Detected From New User Input : ", topic)
                #To Be used only for local testing in the absence of Redis:
                session_memory = SessionMemory(current_topic=topic,
                                               interview_state=InterviewState.INTERVIEW_STARTED)
                
                await self.mongo_service.update_session_memory(interview_id=state["interview_id"], 
                                                            memory=session_memory)
                
                conversation_context.session_memory.current_topic = response.topic
                return Command(update={
                                "topic" : topic,
                                "response" : message,
                                "topic_switched" : response.topic_switched,
                                "conversation_context" : conversation_context
                                },
                                goto="topic_router")
