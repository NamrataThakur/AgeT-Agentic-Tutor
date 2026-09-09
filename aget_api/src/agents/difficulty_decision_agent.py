from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

import os
import sys
from abc import ABC, abstractmethod

os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from agents.base_agent import BaseAgent
from config.settings import settings
from data_models.difficulty_decision_llm import DifficultyDecisionLLM
from prompts.difficulty_decision_prompt import DIFFICULTY_DECISION_SYSTEM_PROMPT, DIFFICULTY_DECISION_USER_PROMPT


openai_api_key = os.getenv("OPENAI_API_KEY")

class DifficultyDecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(name=settings.MODEL_NAME, 
                                    temperature=settings.MODEL_TEMPERATURE, 
                                    api_key=openai_api_key, 
                                    max_tokens=settings.MAX_TOKENS,
                                    max_retries=settings.MAX_RETRIES)

    
    async def invoke(self, context, prompt):

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", DIFFICULTY_DECISION_SYSTEM_PROMPT),
                                                        ("user", DIFFICULTY_DECISION_USER_PROMPT)
                                                    ]
                                                )
                        
        structured_llm = self.llm.with_structured_output(DifficultyDecisionLLM)

        chain = prompt | structured_llm

        session_memory = context[0]
        episodic_memory = context[1]

        output = await chain.ainvoke(
                                        {
                                            "session_memory": session_memory,
                                            "episodic_memory": episodic_memory
                                        }
                                    )
        print("Target Difficulty Inferred Successfully Using LLM ...!")

        return output