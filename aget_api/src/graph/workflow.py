import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from langgraph.graph import StateGraph, START, END
from graph.router import decision_router, topic_router, resume_router, pause_router, failure_check_router
from graph.state import AgentState
from nodes.planner_node import PlannerNode
from nodes.executor_node import ExecutorNode
from nodes.input_processing_node import InputProcessingNode
from nodes.intent_detector_node import IntentDetectorNode
from nodes.knowledge_service_node import KnowledgeServiceNode
from nodes.memory_node import MemoryManagerNode
from nodes.memory_updation_node import MemoryUpdateNode
from nodes.failure_handler_node import FailureHandlerNode


class GraphBuilder:
    def __init__(self, nodes : dict):
        self.nodes = nodes


    def create_workflow_graph(self):

        graph = StateGraph(AgentState)

        # #Defining Nodes:
        # input_processor = InputProcessingNode()
        # intent_detector = IntentDetectorNode()
        # memory_loader = MemoryManagerNode()
        # failer_handler = FailureHandlerNode()

        # planner = PlannerNode()
        # executor = ExecutorNode()
        # knowledge_node = KnowledgeServiceNode()
        # memory_update = MemoryUpdateNode()

        # knowledge_service = KnowledgeService() #MCP for the knowledge base
        
        #Adding Nodes in the graph:
        graph.add_node("input_processing", self.nodes["input_processor"].execute)
        graph.add_node("intent_detection", self.nodes["intent_detector"].execute) #Intent and Topic Will be detected
        graph.add_node("knowledge_service", self.nodes["knowledge_node"].execute)
        graph.add_node("memory_loader", self.nodes["memory_loader"].execute)
        graph.add_node("failure_handler", self.nodes["failure_handler"].execute)
        graph.add_node("topic_router", topic_router) # Returns Command[Literal["knowledge_service", "planner"]]
        graph.add_node("planner", self.nodes["planner"].execute)
        graph.add_node("executor", self.nodes["executor"].execute)
        graph.add_node("memory_update", self.nodes["memory_update"].execute)

        #Adding edges:
        graph.add_edge(START, "input_processing")
        graph.add_edge("input_processing", "memory_loader")
        graph.add_conditional_edges("memory_loader",
                                    resume_router,
                                    {
                                        "resume" : "knowledge_service",
                                        "failed" : "failure_handler",
                                        "general_workflow" : "intent_detection" 
                                    })
        graph.add_edge("failure_handler", END)
        
        # Intent Detection Returns Command[Literal["topic_router", "__end__"]]
        # Note: No explicit edges are needed out of "intent_detection" or "topic_router"!
        # Their internal Command(goto="...") blocks handle those jumps seamlessly.

        # graph.add_conditional_edges("intent_detection", 
        #                             intent_router, #Router will check last recorded and current intent and topic. 
        #                             {
        #                                 "knowledge" : "knowledge_service",
        #                                 "plan" : "planner"
        #                             }
        #                             )
    
        graph.add_conditional_edges("knowledge_service",
                                    pause_router,
                                    {
                                        "pause" : END,
                                        "ready" : "planner"
                                    })
        
        graph.add_edge("planner", "executor")
        graph.add_conditional_edges("executor",
                                    failure_check_router,
                                    {
                                        "agent_success" : "memory_update", #Memory needs to be updated before routing
                                        "agent_failure" : END
                                    })
        
        #graph.add_edge("executor", "memory_update") 

        graph.add_conditional_edges("memory_update",
                                    decision_router,
                                    {
                                        "continue" : "planner",
                                        "finish" : END
                                    })

        return graph


    def print_graph(self, graph):
        png_data = graph.get_graph().draw_mermaid_png()
        with open("AgeT_graph.png", "wb") as f:
            f.write(png_data)


# ----- Local Testing -----------------------------------------------
# Compiled without a checkpointer. Used for LangGraph Studio
# graph_builder = GraphBuilder(nodes={})
# graph_compiled = graph_builder.create_workflow_graph().compile()
# graph_builder.print_graph(graph=graph_compiled)


