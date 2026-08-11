import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

from transport.base_transport import BaseTransport
from agents.agent_registry import AgentRegistry
from agents.agent_runtime import AgentRuntime
from data_models.agent_context import AgentContext
from data_models.conversation_context import ConversationContext
from graph.state import AgentState


class LocalTransport(BaseTransport):

    def __init__(self, registry : AgentRegistry, runtime : AgentRuntime):
        self.registry = registry
        self.runtime = runtime


    def dispatch(self, state : AgentState, task):

        # Get the required specialised agent using Agent Registry:
        agent = self.registry.discover(
                                        task.skill

                                        )
        # Executor assembles the context into AgentContext object:
        context = AgentContext(
                                    task=task,
                                    agent_conversation_context=state.conversation_context,
                                    state=state
                                )

        
        # AgentRuntime will use agent context and call the required agent:
        response = self.runtime.execute(agent=agent, context = context)

        return response