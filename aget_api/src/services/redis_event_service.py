import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from redis_connection.redis_client import redis_client

class RedisEventService:

    #Redis Stream where job lifecycle events are stored:
    STREAM_NAME = "background:events"

    #Consumer group for the redis stream. These are responsible for processing events:
    CONSUMER_GROUP = "aget-event-consumers"


    def __init__(self, redis_client):

        #Redis is async version here:
        #Note: All further redis calls needs to be awaited
        self.redis = redis_client
        print("Redis Connected..!")


    # ---------------------------------------------------------
    # Publish event
    # ---------------------------------------------------------
    async def publish_events(self, event_type: str, 
                             job_id: str, job_type: str, 
                             user_id:str, interview_id:str, payload:dict):

        event = {
            "event_type" : event_type,
            "job_id" : job_id,
            "job_type" : job_type,
            "user_id" : user_id,
            "interview_id": interview_id,
            "payload" : payload or {}
        }

        #This adds a new entry into the Redis Stream:
        event_id = await self.redis.xadd(name=self.STREAM_NAME, fields=event)

        return event_id


    # ---------------------------------------------------------
    # Create consumer group
    # ---------------------------------------------------------
    async def create_consumer_group(self):

        try:
            await self.redis.xgroup_create(name=self.STREAM_NAME, 
                                           groupname=self.CONSUMER_GROUP,

                                           # Group is positioned at the begining of the stream. 
                                           # It's useful when initially creating the group because 
                                           # it establishes where the consumer group starts reading.
                                           id=0, 

                                           #If the stream doesnt exists, then it first create the stream:
                                           mkstream=True)
            
        except Exception as e:
            # Group already exists
            if "BUSYGROUP" not in str(e):
                raise


    # ---------------------------------------------------------
    # Consume events
    # ---------------------------------------------------------
    async def consume_events(self, consumer_name:str, count: int, block: int):

        events = await self.redis.xreadgroup(groupname=self.CONSUMER_GROUP,
                                             consumername=consumer_name,

                                             #Give this consumer messages that are new to the consumer group.
                                             streams={
                                                 self.STREAM_NAME: ">"
                                             },

                                             #The consumer can request up to 'n' events at a time.
                                             count=count,
                                             
                                             #Wait up to 'm' seconds for an event if there isn't one available immediately.
                                             block=block
                                             )


        return events


    # ---------------------------------------------------------
    # Acknowledge event
    # ---------------------------------------------------------
    async def acknowledge_events(self, event_id : str):

        await self.redis.xack(event_id, name=self.STREAM_NAME,groupname=self.CONSUMER_GROUP)
        



    

    


    