from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings
from graph.state import AgentState
from data_models.topic_detector import TopicStwichDetection
from prompts.topic_switch_detection_prompt import TOPIC_SWITCH_DETECTION_SYSTEM_PROMPT, TOPIC_SWITCH_DETECTION_USER_PROMPT

openai_api_key = os.getenv("OPENAI_API_KEY")


class IntentDetectionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(name=settings.MODEL_NAME, 
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)


    async def invoke(self, state : AgentState) -> TopicStwichDetection:

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", TOPIC_SWITCH_DETECTION_SYSTEM_PROMPT),
                                                        ("user", TOPIC_SWITCH_DETECTION_USER_PROMPT)
                                                    ]
                                                )
                
        structured_llm = self.llm.with_structured_output(TopicStwichDetection)

        relation_chain = prompt | structured_llm

        current_topic = state["conversation_context"].session_memory.current_topic

        topic_switch_output = await relation_chain.ainvoke(
                                                            {
                                                                "user_input": state["user_input"],
                                                                "last_topic": current_topic
                                                            }
                                                        )
        print("Topic and Switch Detection Executed Successfully Using LLM ...!")

        return topic_switch_output