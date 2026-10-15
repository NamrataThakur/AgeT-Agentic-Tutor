import uuid
import asyncio
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.redis_event_service import RedisEventService
from config.settings import settings
from event_handler import EventHandler

class RedisEventConsumer:
    def __init__(self, event_service : RedisEventService, event_handler : EventHandler):
        self.event_service = event_service
        self.consumer_name = f"consumer-{uuid.uuid4().hex}"
        self.event_handler = event_handler

        self.running = False
        self.task = None    

    
    #App Container will start the consumer queue during application startup:
    async def start(self):

        self.running = True
        self.task = asyncio.create_task(self.run())

    #App Container will stop the consumer queue during application close:
    async def stop(self):
        self.running = False

        if self.task:
            await self.task
            self.task = None


    #This is called when the FastAPI Application starts through the container's startup function:
    async def run(self):

        await self.event_service.create_consumer_group()

        while self.running:

            events = await self.event_service.consume_events(consumer_name=self.consumer_name,
                                                             count=settings.REDIS_CONSUMER_MAX_EVENT,
                                                             block=settings.REDIS_CONSUMER_BLOCK_SECS)
            if not events:
                continue

            #It will parse the events and call the event handler to sent the SSE notifications:
            await self.process_events(events=events)

        

    async def process_events(self, events):

        if events:

            #Parsing of the event starts: 
            for stream_name, messages in events:
                print(f"Processing Stream : {stream_name}")

                for message_id, data in messages:

                    try:
                        #Sending the Event Data to the Handler to send the SSE Notification:
                        await self.event_handler.handle(events=data)

                        #Acknowledge the event ONLY when the notification is sent successfully:
                        await self.event_service.acknowledge_events(event_id=message_id)

                    except Exception as e:

                        print(f"Processing the Event with id: {message_id} failed with error : {str(e)}")
                        #Do NOT acknowledgement the event.....

        else:

            print("No Messages In the Event Stream to Parse...!")
    