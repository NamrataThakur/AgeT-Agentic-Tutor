#The manager keeps track of browsers currently listening for events.

import asyncio
from collections import defaultdict
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class ServerSentEventManager:
    def __init__(self):

        #Note: Redis Stream and SSE HTTP Connections are two different and independent async operations:
        #      So asyncio.Queue acts as a bridge between Redis Stream and SSE HTTP Connection.
        #Step 1: Create a dictionary containing a set of SSE queues for each interview id:
        #Note: Each browser connection is one queue, so one interview can have multiple open browser, 
        #                                            so multiple queues for one interview is possible:
        self.clients : dict[str, set[asyncio.Queue]] = defaultdict(set)


    async def connect(self, interview_id : str) -> asyncio.Queue:
        """
        This function is called when the browser calls: GET /events/{interview_id}
        This function creates an asyncio.Queue and assigns it to the interview id 
                       and return the queue to the broswer SSE Endpoint.
        """
        queue = asyncio.Queue
        
        self.clients[interview_id].add(queue)

        print(f"SSE Connected for Interview id: {interview_id}")
        return queue


    async def disconnect(self, interview_id : str, queue: asyncio.Queue):
        """
        This function is called when the browser gets closed or the connection is lost. 
           SSE endpoint detects it and calls the disconnect function.
        We discard the queue that is corresponding to that browser that is closed. 
           In case all browsers for that interview id is closed, it discards the entry for that interview itself.
        """
        self.clients[interview_id].discard(queue)

        if not self.clients[interview_id]:
            del self.clients[interview_id]

        print(f"SSE Connection closed for Interview id: {interview_id}")
    

    async def send(self, interview_id: str, event:dict):
        """
        This function is called from the EventHandler class. 
             It takes the event from the Redis Stream and puts it into the Queue.
        """

        #First get all the queues for the interview id provided:
        queues = self.clients[interview_id]

        #If no queue exists for this interview id, then it means SSE HTTP Connection is not done yet:
        if not queues:
            print(f"SSE Connection DOES NOT Exists for the Interview id: {interview_id}")
            return

        #Iterates over the queues that exists:
        for queue in list(queues):
            #Put the event into each queue, so that each SSE HTTP Connection can consume it:
            await queue.put(event)
