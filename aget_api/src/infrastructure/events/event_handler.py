#The published Redis event becomes an SSE notification through this handler.

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from server_sent_events.sse_manager import ServerSentEventManager


class EventHandler:
    def __init__(self, sse_manager : ServerSentEventManager):
        self.sse_manager = sse_manager


    async def handle(self, events:dict):

        event_type = events["event_type"]

        if event_type == "job.completed":
            await self.success_handler(events=events)

        elif event_type == "job.failed":
            await self.failure_handler(events=events)

        else:
            raise ValueError(f"Unknown Event Type Detected in the message : {event_type}")

    
    
    async def success_handler(self, events):

        interview_id = events["interview_id"]

        event_info = {
            "event_type" : events["event_type"],
            "data" : {
                "interview_id" : events["interview_id"],
                "job_id" : events["job_id"],
                "user_id" : events["user_id"],
                "message" : events["payload"]["result"]
            } 
        }

        await self.sse_manager.send(interview_id=interview_id, event=event_info)
        

    async def failure_handler(self, events):

        interview_id = events["interview_id"]
        
        event_info = {
            "event_type" : events["event_type"],
            "data" : {
                "interview_id" : events["interview_id"],
                "job_id" : events["job_id"],
                "error_message" : events["payload"]["result"],
                "message" : "Question Bank Generation Failed."
            } 
        }

        await self.sse_manager.send(interview_id=interview_id, event=event_info)