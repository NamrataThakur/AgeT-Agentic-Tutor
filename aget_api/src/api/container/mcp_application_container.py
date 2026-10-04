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
from question_generator.question_generation_pipeline import QuestionFullGenerationPipeline
from services.question_bank_service import QsBankService
from services.redis_service import RedisService
from redis.redis_client import redis_client

#---- Loading ALL Infrastructure Details ------
#---- Background --------
from infrastructure.background.executor import BackgroundExecutor
from infrastructure.background.job_manager import JobManager
from infrastructure.background.registry import WorkerRegistry

#---- Worker --------
from infrastructure.workers.qs_bank_worker import QsBankWorker
from infrastructure.workers.bucket_regen_worker import BucketRegenWorker

from knowledge_mcp.tools.get_question_bank import GetQuestionBankTool
from knowledge_mcp.tools.create_question_bank import CreateQuestionBankTool



class MCPApplicationContainer:
    def __init__(self):

        # ==================================================
        # 1. Redis
        # ==================================================
        self.redis = redis_client

        # ==================================================
        # 2. Services
        # ==================================================
        self.redis_service = RedisService(redis_client=self.redis)
        
        # ==================================================
        # 3. Infrastructure and Background Job System
        # ==================================================
        
        self.job_manager = JobManager(redis_service=self.redis_service)
        
        self.qs_gen_worker = QsBankWorker(question_service=self.question_bank_gen_service,
                                            job_manager=self.job_manager,
                                            redis_service=self.redis_service,
                                            event_service=self.event_service)

        self.worker_registry = WorkerRegistry()
        
        self.worker_registry.register(task_name="create_question_bank",
                                        worker=self.qs_gen_worker)

        self.background_executor = BackgroundExecutor(registry=self.worker_registry)
        
        qs_gen = QuestionFullGenerationPipeline(db=self.db)

        self.question_bank_gen_service = QsBankService(db = self.db,
                                                        qs_generator=qs_gen)

        self.get_question_bank_tool = GetQuestionBankTool(qs_service=self.question_bank_gen_service,
                                                          job_manager=self.job_manager,
                                                          executor=self.background_executor)

        self.create_question_bank_tool = CreateQuestionBankTool(qs_service=self.question_bank_gen_service,
                                                                job_manager=self.job_manager,
                                                                executor=self.background_executor)

        