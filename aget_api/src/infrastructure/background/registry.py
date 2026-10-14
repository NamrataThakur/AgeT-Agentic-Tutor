from collections.abc import Awaitable, Callable
from typing import Any
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from infrastructure.workers.qs_bank_worker import QsBankWorker
from infrastructure.workers.bucket_regen_worker import BucketRegenWorker


JobHandler = Callable[[dict[str, Any]], Awaitable[Any],]


class WorkerRegistry:
    def __init__(self):
        self.workers : dict[ str, JobHandler] = {}
        

    async def register(self, task_name: str, worker: JobHandler):

        if task_name in self.workers:
            raise ValueError(f"Worker for {task_name} already exists in the Job Registry..!")

        self.workers[task_name] = worker


    async def get(self, task_name: str) -> JobHandler:

        if task_name not in self.workers:
            raise ValueError(f"Worker for {task_name} NOT registered in the Job Registry..!")

        return self.workers[task_name]