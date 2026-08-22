import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from context_builder.context_builder_registry import ContextBuilderRegistry
from data_models.execution_result import AgentType
from data_models.agent_context import AgentContext

class ContextService:
    def __init__(self):
        #The context builder registry that will map agent name with the class name for the CB for that agent
        self.context_registry = ContextBuilderRegistry()
       

    def load_context(self, agent_name : str, context : AgentContext):
        # Check if we have builder for this agent:
        if self.context_registry.has_builder(agent_name=agent_name):

            # With the agent name, check the CB registry and load the builder. 
            builder = self.context_registry.get_builder(agent_name=agent_name)
            
        else: 
            raise ValueError(f"No context builder registered for agent: {agent_name}")

        # Call the builder's function i.e. build_context using common context to agent specific context:
        context = builder.build_context(common_context=context)

        return context