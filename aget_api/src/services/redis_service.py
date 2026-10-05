from pydantic import BaseModel
import json
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from redis_connection.redis_client import redis_client


class RedisService:
    def __init__(self, redis_client):

        #Redis is async version here:
        #Note: All further redis calls needs to be awaited
        self.redis = redis_client
        print("Redis Connected..!")


    def create_composite_key(self, interview_id : str, user_id: str, content_type : str) -> str:

        if content_type == "interview":
            composite_key = f"interview-episode:{user_id}:{interview_id}"
        else:
            composite_key = f"resume-episode:{user_id}:{interview_id}"

        return composite_key


    async def get_interview(self, interview_id : str, user_id: str, context_model : type[BaseModel]) -> BaseModel | None:
        """
        Get the conversation context (saved in the redis)
        for graph hydration process of the provided user and interview episode
        This is called from "memory_loader" node
        """

        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                  user_id=user_id,
                                                  content_type = "interview")

        redis_data = await self.redis.hgetall(composite_key)

        if not redis_data:
            return None

        data = {
            key : json.loads(value)
            for key, value in redis_data.items()
        }

        model = context_model.model_validate(data)

        return model


    async def save_interview(self, user_id: str, interview_id : str, context : BaseModel):
        """
        Save the final conversation context at the end of a turn to be loaded later 
        for graph hydration process of the provided user and interview episode
        This is called from "memory_update", "knowledge_service" and "failure_handler" nodes.
        """
        
        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                  user_id=user_id,
                                                  content_type = "interview")

        if not context:
            raise ValueError("Context to be saved CANNOT be None..!")
        
        data = context.model_dump()

        redis_data = {
            key : json.dumps(value)
            for key, value in data.items()
        }

        await self.redis.hset(composite_key, mapping = redis_data)

        return "Interview Saved to Redis..!"
    

    async def delete_interview(self, user_id: str, interview_id : str):
        """
        delete the final conversation context at the end of a complete interview episode. 
        To be called during application shutdown.
        """
        
        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                  user_id=user_id,
                                                  content_type = "interview")

        result = await self.redis.delete(composite_key)

        return result > 0

    
    async def get_resumeState(self, interview_id : str, user_id : str, context_model : type[BaseModel])-> BaseModel | None:
        """
        Get the resume state (saved in the redis) for graph hydration process 
        of the provided user and interview episode.
        This is required for the pause/resume workflow logic
        This is called from the "memory_loader" node.
        """

        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                user_id=user_id,
                                                content_type = "resume")

        redis_data = await self.redis.hgetall(composite_key)

        if not redis_data:
            return None

        data = {
                    key : json.loads(value)
                    for key, value in redis_data.items()
                }

        model = context_model.model_validate(data)

        return model


    async def save_resumeState(self, interview_id : str, user_id : str, context : BaseModel):
        """
        Save the final conversation context at the end of a turn to be loaded later 
        for graph hydration process of the provided user and interview episode
        This is called from the background worker (for statuses "running", "ready" or "failed") 
                and from "knowledge_service" node (for status "consumed")
        """

        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                user_id=user_id,
                                                content_type = "resume")

        if not context:
            raise ValueError("Context for saving resume state CANNOT be None..!")

        data = context.model_dump()

        redis_data = {
                    key : json.dumps(value)
                    for key, value in data.items()
                }

        await self.redis.hset(composite_key, mapping = redis_data)

        return "Resume State Saved to Redis..! Interview can be paused..."


    async def clear_resumeState(self, interview_id : str, user_id : str) -> bool:
        """
        Delete the resume state when the background job failed. 
        To be called during failure handler node.
        This is called from "failure_handler" node.
        """

        composite_key = self.create_composite_key(interview_id=interview_id, 
                                                user_id=user_id,
                                                content_type = "resume")

        result = await self.redis.delete(composite_key)

        return result > 0

    
    async def create_job(self, job_key: str, context : BaseModel):

        if not context:
            raise ValueError("Context required to create a job ..!")

        data = context.model_dump()

        redis_data = {
                        key : json.dumps(value)
                        for key, value in data.items()
                    }

        await self.redis.hset(job_key, mapping=redis_data)

        return "Job created..!"


    async def get_job(self, key: str, context_model : type[BaseModel]) -> BaseModel | None:

        job_info = await self.redis.hgetall(key)

        if not job_info :
            return None

        data = {
                    key : json.loads(value)
                    for key, value in job_info.items()
                }
        
        job = context_model.model_validate(data)

        return job


    async def set_secondary_key(self, secondary_key : str, primary_key : str ):

        await self.redis.set(secondary_key, primary_key)

        return "Secondary Key Set ..!"


    async def get_primary_key(self, secondary_key : str):

        primary_key = await self.redis.get(secondary_key)

        return primary_key
    

    async def set_status(self, key: str, context : dict):

        if not context:
            raise ValueError("Context is required to update/set the status of the job ...!")

        await self.redis.hset(key, mapping=context)

        return "Status is updated ..!"


if __name__ == "__main__":
    r = RedisService()