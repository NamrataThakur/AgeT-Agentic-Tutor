import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from agents.executor_agent import ExecutorAgent

# STEPS THAT ARE PRESENT WITHIN EXECUTOR AGENT. EXECUTOR NODE IS A THIN WRAPPER OVER THE EXECUTOR AGENT:
# ┌─────────────────────────────────────────────┐
# │                 EXECUTOR AGENT              │
# │                                             │
# │  1. Prepare ExecutionRuntime                │
# │  2. Read Planner output                     │
# │  3. Resolve next executable task            |
# │  4. Build A2ATask                           │
# │  5. Dispatch via Transport                  │
# └──────────────────────┬──────────────────────┘
#                        │
#                        ▼
# ┌─────────────────────────────────────────────┐
# │                  TRANSPORT                  │
# │                                             │
# │  6. Resolve agent via Agent Registry        │
# │  7. Build AgentContext                      │
# │  8. Call AgentRuntime                       │
# └──────────────────────┬──────────────────────┘
#                        │
#                        ▼
# ┌─────────────────────────────────────────────┐
# │                AGENT RUNTIME                │
# │                                             │
# │  9. Resolve/load prompt                     │
# │ 10. Prepare agent execution context         │
# │ 11. Invoke specialised agent                │ 
# │ 12. Validate structured output              │
# │ 13. Return validated result                 │ 
# └──────────────────────┬──────────────────────┘
#                        │
#                        ▼
# ┌─────────────────────────────────────────────┐
# │                 TRANSPORT                   │
# │                                             │
# │  14. Construct/return A2AResponse           │
# └──────────────────────┬──────────────────────┘
#                        │
#                        ▼
# ┌─────────────────────────────────────────────┐
# │                 EXECUTOR AGENT              │
# │                                             │
# │ 15. Convert A2AResponse → ExecutionResult   │
# │ 16. Update LangGraph State                  │
# └─────────────────────────────────────────────┘

class ExecutorNode:
    def __init__(self, executor_agent : ExecutorAgent):
        self.executor_agent = executor_agent

    async def execute(self, state : AgentState) -> dict:

        conversation_context = state["conversation_context"]
        execution_result = await self.executor_agent.execute(state=state)

        #Updating the session memory with the execution results
        conversation_context.session_memory.last_execution_result = execution_result

        return {
            "execution_result" : execution_result,
            "conversation_context" : conversation_context,
            "response" : execution_result.response
        }