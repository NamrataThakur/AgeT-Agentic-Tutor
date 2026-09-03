import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from langgraph.graph import StateGraph, START, END
from graph.router import decision_router, topic_router
from graph.state import AgentState
from nodes.planner_node import PlannerNode
from nodes.executor_node import ExecutorNode
from nodes.input_processing_node import InputProcessingNode
from nodes.intent_detector_node import IntentDetectorNode
from nodes.knowledge_service_node import KnowledgeServiceNode
from nodes.memory_node import MemoryManagerNode
from nodes.memory_updation_node import MemoryUpdateNode

from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.intent_detector_agent import IntentDetectionAgent

from services.knowledge_service import KnowledgeService
from services.memory_service import MemoryService

def create_workflow_graph():

    graph = StateGraph(AgentState)

    #Defining Nodes:
    input_processor = InputProcessingNode()
    intent_detector = IntentDetectorNode()
    memory_loader = MemoryManagerNode()

    planner = PlannerNode()
    executor = ExecutorNode()
    knowledge_node = KnowledgeServiceNode()
    memory_update = MemoryUpdateNode()

    # knowledge_service = KnowledgeService() #MCP for the knowledge base
    
    #Adding Nodes in the graph:
    graph.add_node("input_processing", input_processor.execute)
    graph.add_node("intent_detection", intent_detector.execute) #Intent and Topic Will be detected
    graph.add_node("knowledge_service", knowledge_node.execute)
    graph.add_node("memory_loader", memory_loader.execute)
    graph.add_node("topic_router", topic_router) # Returns Command[Literal["knowledge_service", "planner"]]
    graph.add_node("planner", planner.execute)
    graph.add_node("executor", executor.execute)
    graph.add_node("memory_update", memory_update.execute)

    #Adding edges:
    graph.add_edge(START, "input_processing")
    graph.add_edge("input_processing", "memory_loader")
    graph.add_edge("memory_loader", "intent_detection") # Intent Detection Returns Command[Literal["topic_router", "__end__"]]
    # Note: No explicit edges are needed out of "intent_detection" or "topic_router"!
    # Their internal Command(goto="...") blocks handle those jumps seamlessly.

    # graph.add_conditional_edges("intent_detection", 
    #                             intent_router, #Router will check last recorded and current intent and topic. 
    #                             {
    #                                 "knowledge" : "knowledge_service",
    #                                 "plan" : "planner"
    #                             }
    #                             )
   

    graph.add_edge("knowledge_service","planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", "memory_update") #Memory needs to be updated before routing
    graph.add_conditional_edges("memory_update",
                                decision_router,
                                {
                                    "continue" : "planner",
                                    "finish" : END
                                })

    return graph

# Compiled without a checkpointer. Used for LangGraph Studio
graph_compiled = create_workflow_graph().compile()