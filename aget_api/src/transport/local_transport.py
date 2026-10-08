import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from transport.base_transport import BaseTransport
from agents.agent_registry import AgentRegistry
from agents.agent_runtime import AgentRuntime
from data_models.a2a_response import A2AResponse
from data_models.a2a_task import A2ATask
from graph.state import AgentState

#TASKS IN TRANSPORT:
# 1. Resolve agent via Agent Registry
# 2. Build AgentContext
# 3. Call AgentRuntime
class LocalTransport(BaseTransport):

    def __init__(self, registry : AgentRegistry, runtime : AgentRuntime):
        self.registry = registry
        self.runtime = runtime


    async def dispatch(self, state : AgentState, task : A2ATask) -> A2AResponse:

        # Get the required specialised agent using Agent Registry:
        agent = self.registry.discover(
                                        task.skill
                                        )

        
        # AgentRuntime will use agent context and call the required agent:
        response = await self.runtime.execute(agent=agent, state = state, task = task)

        return response