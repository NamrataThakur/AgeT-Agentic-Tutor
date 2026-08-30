from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
import asyncio
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

from agents.agent_runtime import AgentRuntime
from data_models.agent_skills import AgentSkill
from data_models.a2a_response import A2AResponse
from agents.agent_registry import AgentRegistry


openai_api_key = os.getenv("OPENAI_API_KEY")

class SummaryService:
    def __init__(self):
        self.runtime = AgentRuntime()
        self.registry = AgentRegistry()

    async def execute(self, context, skill : AgentSkill) -> A2AResponse:

        #Step 1: Get a SummaryAgent Object to pass in runtime:
        # Get the required specialised agent using Agent Registry:
        agent = self.registry.discover(skill)
        
        #Step 2: Call AgentRuntime with no A2ATask and AgentState
        # AgentRuntime will use agent context and call the required agent:
        response = await self.runtime.execute(agent=agent, context=context)

        #Step 3: Return A2AResponse:
        return response

