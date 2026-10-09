#This file handles the background job creation, querying the job status etc. 
# It helps to prevent duplicate generation jobs and uses Redis. 
# It does not know anything about question banks, buckets, knowledge bases, or maintenance.

import uuid
from datetime import datetime, timezone
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.redis_service import RedisService
from infrastructure.background.job_model import JobStatus, BackgroundJob


class JobManager:
    def __init__(self, redis_service : RedisService):
        self.redis_service = redis_service
        self.active_statuses = {"pending", "running", "regenerating"}

    def get_job_key(self, job_id:str):

        key = f"background:job:{job_id}"
        return key

    def get_dedup_key(self, topic:str, task_name:str, bucket:str | None ):

        key = f"background:dedup:{task_name}:{topic}:{bucket}" if bucket else f"background:dedup:{task_name}:{topic}"
        return key


    @staticmethod
    def decode(self, value):
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    
    async def get_active_job(self, topic: str, task_name:str, bucket:str | None):
        """
        Return the active job associated with a deduplication key. 
        Deduplication key is created using topic, type and bucket value
        """

        #Topic: topic_id, Type: qsgeneration or bucketregeneration

        #Step 1: Using the topic, type and bucket, construct the dedup key.
        dedup_key = await self.get_dedup_key(topic=topic, task_name=task_name, bucket=bucket)

        #Step 2: Use the de-duplication key to get the corresponding job id:       
        job_id = await self.redis_service.get_primary_key(secondary_key=dedup_key)

        # job_id = await self.redis_service.get(dedup_key)

        #If there is no job for the topic provided:
        if not job_id:
            return None

        #If there is a job, then decode the job id incase redis is storing it in bytes:
        job_id = self.decode(job_id)

        #Step 3: Using the job id, get the full job info:
        job = self.get_job(job_id=job_id, task_name=task_name)

        #Then check the status:
        job_status = job.get("status", "")

        #If the status is not among the active running status, then the job is finished and it is not active anymore:
        if job_status not in self.active_statuses:
            return None

        return job


    async def create_job(self, job: BackgroundJob):


        #Type: qsgeneration or bucketregeneration

        #Step 1: Check if any existing job is running for the topic provided:
        existing_job = await self.get_active_job(topic=job.topic, task_name=job.task_name, bucket=job.bucket)

        if existing_job:
            return existing_job

        #Step 2: No existing job. SO create a job for the topic provided:
        #Create the unique job id
        job_id = str(uuid.uuid4())

        #Create the job key for the topic:
        job_key = await self.get_job_key(jobId=job_id)
        
        #Create the De-Duplication Key:
        dedup_key = self.get_dedup_key(topic=job.topic, task_name=job.task_name, bucket=job.bucket)

        #Update Redis:
        job_info = {
                        "job_id" : job_id, #Use the unique job id string here and not the job key
                        "dedup_key" : dedup_key,
                        "topic" : job.topic,
                        "bucket" : job.bucket,
                        "task_name" : job.task_name,
                        "status" : JobStatus.PENDING,
                        "eta_seconds" : job.eta_secs,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }

        job_model = BackgroundJob.model_validate(job_info)

        #Create the Redis Hash corresponding the job key:
        await self.redis_service.create_job(key=job_key, context=job_model)

        # await self.redis_service.hset(
        #     job_key,
        #     mapping = job_info
        #     )

        #Set the mapping between deduplication key (secondary key) and the job id (primary key):
        await self.redis_service.set_secondary_key(secondary_key=dedup_key, primary_key=job_id)


        # await self.redis_service.set(
        #     dedup_key,
        #     job_id
        # )

        return job_info


    #Update the Job Status to "running" when the job has started successfully:
    async def mark_running(self, job_id: str):

        job_key = await self.get_job_key(job_id=job_id)

        await self.redis_service.set_status(key = job_key, 
                                            context = 
                                            {
                                                "status" : JobStatus.RUNNING,
                                                "started_at": datetime.now(timezone.utc).isoformat(),
                                            }
                                        )

        
        # await self.redis_service.hset(
        #     job_key, 
        #     mapping = 
        #     {
        #         "status" : JobStatus.RUNNING,
        #         "started_at": datetime.now(timezone.utc).isoformat(),
        #     }
        # )


    #Update the Job Status to "ready" when the job is completed successfully:
    async def mark_ready(self, job_id: str, result: dict):

        job_key = await self.get_job_key(job_id=job_id)

        await self.redis_service.set_status(key = job_key, 
                                            context = 
                                            {
                                                "status" : JobStatus.READY,
                                                "result" : result.message,
                                                "completed_at": datetime.now(timezone.utc).isoformat(),
                                            }
                                        )
        
        # await self.redis_service.hset(
        #     job_key, 
        #     mapping = 
        #     {
        #         "status" : JobStatus.READY,
        #         "result" : result,
        #         "completed_at": datetime.now(timezone.utc).isoformat(),
        #     }
        # )


    #Update the Job Status to "failed" when the job has thrown error:
    async def mark_failed(self, job_id:str, error:str):

        job_key = await self.get_job_key(job_id=job_id)

        await self.redis_service.set_status(key = job_key, 
                                            context = 
                                            {
                                                "status" : JobStatus.FAILED,
                                                "error": error,
                                                "completed_at": datetime.now(timezone.utc).isoformat(),
                                            }
                                        )
        
        # await self.redis_service.hset(
        #     job_key, 
        #     mapping = 
        #     {
        #         "status" : JobStatus.FAILED,
        #         "error": error,
        #         "completed_at": datetime.now(timezone.utc).isoformat(),
        #     }
        # )


    #Update the Job Status to "regenerating" when the job is about regenerating bucket or question bank:
    async def mark_regenerate(self, job_id:str):

        job_key = await self.get_job_key(job_id=job_id)

        await self.redis_service.set_status(key = job_key, 
                                            context = 
                                            {
                                                "status" : JobStatus.REGENERATE
                                            }
                                        )
        
        # await self.redis_service.hset(
        #     job_key, 
        #     mapping = 
        #     {
        #         "status" : JobStatus.REGENERATE
        #     }
        # )


    async def get_job(self, job_id: str) -> BackgroundJob | None:

        #Step 4: Use the job id to construct the job key (same form that was used when we called 'HSET')
        job_key = self.get_job_key(job_id=job_id)

        #Step 5: Using the job key, fetch entire job info:
        data = self.redis_service.get_job(key=job_key, context_model = BackgroundJob)

        #data = self.redis_service.hgetall(job_key)

        #If there is no job for the topic provided:
        if not data:
            return None

        # Redis may return bytes depending on configuration.
        job = {
            self.decode(key) : self.decode(val) 
            for key, val in data.items()
        }

        job = BackgroundJob.model_validate_json(job)

        return job


        



