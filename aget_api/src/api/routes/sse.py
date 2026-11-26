from fastapi import APIRouter,Request, Depends

import json
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from application.interview_service import InterviewService
from sse_starlette.sse import EventSourceResponse
from infrastructure.server_sent_events.sse_manager import ServerSentEventManager
from api.container.application_container import ApplicationContainer
from api.dependency import get_container

router = APIRouter(prefix="/events", tags=["events"])


async def event_generator(interview_id, queue, request : Request, container : ApplicationContainer):

    try:
        while True:
            if await request.is_disconnected():
                break

            result = await queue.get()

            yield {
                "event" : result["event_type"],
                "data" : json.dumps(result["data"])
            }
    finally:
        await container.sse_manager.disconnect(interview_id=interview_id, queue=queue)



@router.get("/{interview_id}")
async def interview_starts(interview_id : str, request: Request, 
                            container : ApplicationContainer = Depends(get_container)):


    #Start the SSE HTTP Connection:
    queue = await container.sse_manager.connect(interview_id=interview_id)

    return EventSourceResponse(event_generator(interview_id=interview_id, 
                                            queue=queue, 
                                            request=request,
                                            container=container))



