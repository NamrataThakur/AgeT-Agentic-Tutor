import asyncio
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from infrastructure.background.registry import WorkerRegistry
from config.settings import settings

class BackgroundExecutor:
    def __init__(self, registry : WorkerRegistry):
        self.job_registry = registry
        self.max_concurrency = settings.MAX_CONCURRENCY

        self.semaphore = asyncio.Semaphore(value=self.max_concurrency)
        self.tasks : set[asyncio.Task] = set()

    async def submit(self, task_name: str, payload: dict):

        task = asyncio.create_task(
            self.execute(task_name=task_name, payload=payload)
        )

        self.tasks.add(task)

        task.add_done_callback(self.tasks.discard)


    async def execute(self, task_name: str, payload: dict):

        async with self.semaphore:
            worker = self.job_registry.get(task_name)

            await worker(**payload)

