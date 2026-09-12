import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from agents.base_agent import BaseAgent
from agents.agent_registry import AgentRegistry
from agents.agent_runtime import AgentRuntime
from graph.state import AgentState
from data_models.execution_result import ExecutionResult
from data_models.a2a_task import A2ATask
from transport.local_transport import LocalTransport

class ExecutorAgent:
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.agent_runtime = AgentRuntime()
        self.transport = LocalTransport(registry=self.agent_registry, runtime=self.agent_runtime)

    async def execute(self, state : AgentState):

        # Step 1: Prepare ExecutionRuntime --> Tracing + Middleware

        # Step 2: Extract the plan that Planner created:
        plan = state["execution_plan"]

        # Step 3: Prepare the A2ATask object required by the Transport:
        task = A2ATask(
            sender="Executor",
            skill=plan.skill,
            action=plan.action,
            payload=plan.inputs)


        # Step 4: A2A Dispatch over the Transport to call required Specialised Agent:
        response = await self.transport.dispatch(state=state, task=task)

        # Step 5: Prepare the ExecutionResult object using the A2A Response:
        execution_result = ExecutionResult(
            agent_name=response.agent_name,
            agent_skill=response.agent_skill,
            user_input=state["user_input"],
            success=response.success,
            event=response.event,
            response=response.response.data,
            metadata=response.metadata,
            update_memory=False #This will be updated in the next Decision Router Node
        )

        return execution_result
