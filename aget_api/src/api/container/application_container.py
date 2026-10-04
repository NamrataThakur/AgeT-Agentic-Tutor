from __future__ import annotations
from typing import Optional

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

from db.mongo import MongoDb
from redis.redis_client import redis_client

#---- Loading ALL Services ------
from services.context_service import ContextService
from services.failure_recovery_service import FailureRecoveryService
from services.knowledge_service import KnowledgeService
from services.memory_service import MemoryService
from services.mongodb_service import MongoDBService
from services.prompt_service import PromptService
from services.question_bank_service import QsBankService
from services.redis_event_service import RedisEventService
from services.summary_service import SummaryService
from services.redis_service import RedisService

#---- Loading ALL Context Builders ------
from context_builder.base_context_builder import BaseContextBuilder
from context_builder.context_builder_registry import ContextBuilderRegistry
from context_builder.eval_agent_context_builder import EvalAgentContextBuilder
from context_builder.explanation_agent_context_builder import ExplanationAgentContextBuilder
from context_builder.hint_agent_context_builder import HintAgentContextBuilder
from context_builder.question_agent_context_builder import QuestionAgentContextBuilder
from context_builder.summary_agent_context_builder import SummaryAgentContextBuilder

#---- Loading ALL Transports ------
from transport.base_transport import BaseTransport
from transport.local_transport import LocalTransport

#---- Loading Question Bank Generator ------
from question_generator.question_generation_pipeline import QuestionFullGenerationPipeline

#---- Loading ALL Agents ------
from agents.agent_registry import AgentRegistry
from agents.agent_runtime import AgentRuntime
from agents.base_agent import BaseAgent
from agents.question_agent import QuestionAgent
from agents.evaluation_agent import EvaluationAgent
from agents.executor_agent import ExecutorAgent
from agents.explanation_agent import ExplanationAgent
from agents.hint_agent import HintAgent
from agents.intent_detector_agent import IntentDetectionAgent
from agents.planner_agent import PlannerAgent
from agents.planner_policy import PlannerPolicy
from agents.summary_agent import SummaryAgent

#---- Loading ALL Nodes ------
from nodes.executor_node import ExecutorNode
from nodes.failure_handler_node import FailureHandlerNode
from nodes.input_processing_node import InputProcessingNode
from nodes.intent_detector_node import IntentDetectorNode
from nodes.knowledge_service_node import KnowledgeServiceNode
from nodes.memory_node import MemoryManagerNode
from nodes.memory_updation_node import MemoryUpdateNode
from nodes.planner_node import PlannerNode

#---- Loading Langgraph Builder ------
from graph.workflow import GraphBuilder

#---- Loading ALL Infrastructure Details ------
#---- Background --------
from infrastructure.background.executor import BackgroundExecutor
from infrastructure.background.job_manager import JobManager
from infrastructure.background.job_model import BackgroundJob
from infrastructure.background.registry import WorkerRegistry

#---- Events --------
from infrastructure.events.event_handler import EventHandler
from infrastructure.events.redis_event_consumer import RedisEventConsumer

#---- SSE Manager --------
from infrastructure.server_sent_events.sse_manager import ServerSentEventManager

#---- Worker --------
from infrastructure.workers.qs_bank_worker import QsBankWorker
from infrastructure.workers.bucket_regen_worker import BucketRegenWorker

#---- MCP --------
from clients.knowledge_mcp_client import KnowledgeMCPClient


class ApplicationContainer:
    def __init__(self):

        self.settings = settings

        # ==================================================
        # 1. MongoDB
        # ==================================================
        self.db = MongoDb()

        # ==================================================
        # 2. Redis
        # ==================================================
        self.redis = redis_client

        # ==================================================
        # 3. Context Builders
        # ==================================================
        self.context_builder_registry = ContextBuilderRegistry()
        
        self.context_builder_registry.register(agent_name="QuestionAgent",
                                               builder=QuestionAgentContextBuilder())
        
        self.context_builder_registry.register(agent_name="EvaluationAgent",
                                                builder=EvalAgentContextBuilder())

        self.context_builder_registry.register(agent_name="HintAgent",
                                                builder=HintAgentContextBuilder())

        self.context_builder_registry.register(agent_name="ExplanationAgent",
                                                builder=ExplanationAgentContextBuilder())

        self.context_builder_registry.register(agent_name="SummaryAgent",
                                                builder=SummaryAgentContextBuilder())

        # ==================================================
        # 4. Agent Runtime
        # ==================================================
        self.context_service = ContextService(context_builder_registry=self.context_builder_registry)
        self.prompt_service = PromptService(db=self.db)
        self.agent_runtime = AgentRuntime(prompt_service=self.prompt_service,
                                          context_service=self.context_service)

        # ==================================================
        # 5. Agents, Agent Registry and Agent Runtime
        # ==================================================
        self.agent_registry = AgentRegistry()
        self.agent_registry.register(agent=QuestionAgent())
        self.agent_registry.register(agent=HintAgent())
        self.agent_registry.register(agent=ExplanationAgent())
        self.agent_registry.register(agent=EvaluationAgent())
        self.agent_registry.register(agent=SummaryAgent())

        self.intent_detector_agent = IntentDetectionAgent()
        self.planner_agent = PlannerAgent()
        self.plan_policy = PlannerPolicy()


        # ==================================================
        # 6. Transport and Executor Agent
        # ==================================================
        self.transport = LocalTransport(registry=self.agent_registry,
                                        runtime=self.agent_runtime)

        self.executor_agent = ExecutorAgent(transport=self.transport)

        # ==================================================
        # 7. Services
        # ==================================================
        self.redis_service = RedisService(redis_client=self.redis)
        self.failure_handler_service = FailureRecoveryService(redis_service=self.redis_service)
        self.mongo_service = MongoDBService(db=self.db)

        self.summary_service = SummaryService(runtime=self.agent_runtime,
                                              registry=self.agent_registry)
        
        self.memory_service = MemoryService(redis_service=self.redis_service,
                                            db_service=self.mongo_service,
                                            summary_service=self.summary_service)

        self.event_service = RedisEventService(redis_client=self.redis)

        # qs_gen = QuestionFullGenerationPipeline(db=self.db)
        # self.question_bank_gen_service = QsBankService(db = self.db,
        #                                                qs_generator=qs_gen)

        # ==================================================
        # 8. Knowledge MCP Client and Knowledge Service
        # ==================================================
        self.mcp_client = KnowledgeMCPClient(server_command=self.settings.MCP_SERVER_COMMAND,
                                           server_args=self.settings.MCP_SERVER_ARGS)
        
        self.knowledge_service = KnowledgeService(mcp_client=self.mcp_client,
                                                  redis_service=self.redis_service)

        

        


        

        
        

        
        
        



        

