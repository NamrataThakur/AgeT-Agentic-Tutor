from typing import List, Dict

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from knowledge_mcp.schema import GetQSBankRequest, GetQSBankResponse
from clients.knowledge_mcp_client import KnowledgeMCPClient
from config.settings import settings
from services.redis_service import RedisService
from data_models.session_memory import InterviewStatus



#------------------ STEPS ----------------------------------------------------
#PIPELINE DESCRIPTION ::::: 
#Step 1: Knowledge Service Node will call Knowledge Service with agent state: (Done)
#Step 2: Knowledge Service will first connect to the Knowledge MCP Client: (Done)
#Step 3: Knowledge Service will call Knowledge MCP Client for the tool call to see if existing fresh question bank is there for this topic id, (Done)
#        If yes then return the bank (Done)
#Step 4: If not, Knowledge MCP Client will call Knowledge MCP Server for the specific tool to create or regenerate the bank incase it is stale (Done)
#Step 5: Specific MCP Tool is called with Request and Response structure as required (Done)
#Step 6: MCP Tool will call question bank service , create job and update the background executor (Done)
#Step 7: Based on the MCP Tool call result, the response will flow to Knowledge Service Node and state and/or session memory will be updated (Done)
#Step 8: Based on question bank status, the router will be triggered in the workflow --> planner, pause (workflow end but interview running), finish (workflow and interview end) (Done)
#Step 9: Save the conversation_context in Redis
#Step 10: Message to Chainlit -> paused, running, end
#Step 11: UI to continue when job running behind "paused" state is completed. Need to check how to restart UI
#Step 12: IF UI restarted, resume langgraph execution from the InterviewService using same checkpoint session id
#Step 13: Workflow will move from Start -> router (start/resume) -> if start (as existing), if resume then use same state and trigger Knowledge Service Node
#Step 14: Knowledge Service Node will call Knowledge Service with topic id and user input
#Step 15: Get Question Bank Status -> ready . Move to "Planner" and rest works as usual
#Step 16: Update ResumeState object with status as "Consumed" and save in redis for resuming the paused interview: (Done)
#------------------ STEPS ----------------------------------------------------

#After resuming interview, the graph will come here and it will fetch the latest question bank using Knowledge MCP. 
# After that, it will update the redis for the resume state with status as "Consumed"

class KnowledgeService:
    def __init__(self, mcp_client : KnowledgeMCPClient, redis_service: RedisService):
      self.mcp_client = mcp_client 
      self.redis_service = redis_service

    
    async def get_question_bank(self, state: AgentState) -> Dict:

        topic_id = state["conversation_context"].session_memory.current_topic
        user_input = state["user_input"]

        interview_id = state["interview_id"]
        user_id = state["user_id"]

        conversation_context = state["conversation_context"]

        #Step 2: Knowledge Service will first connect to the Knowledge MCP Client:
        await self.mcp_client.connect()

        #Step 3: Knowledge Service will call Knowledge MCP Client for the tool call:
        result = await self.mcp_client.call_tool(tool_name="get_question_bank", 
                                                 args=
                                                    GetQSBankRequest(
                                                        topic_id=topic_id, 
                                                        user_input=user_input,
                                                        user_id=user_id,
                                                        interview_id=interview_id
                                                        )
                                                )
        #If existing fresh question bank is there for this topic id, If yes then return the bank:
        #Knowledge Service will mark the status as "CONSUMED" if resume state is stored in the Redis:
        if result.status == "ready":

            resume_state = state["resume_state"]

            #Step 16: Update ResumeState object with status as "Consumed" and save in redis 
            #         If there is any interview paused to generate the question bank
            if resume_state is not None:
                resume_state.status = "CONSUMED"

                await self.redis_service.save_resumeState(interview_id=interview_id, 
                                                          user_id=user_id,
                                                          context=resume_state)

            context = {
                "topic" : result.topic_id,
                "qs_bank" : result.qs_bank,
                "status" : InterviewStatus.IN_PROGRESS,
                "job_id" : result.job_id,
                "eta_in_secs" : result.eta_in_secs,
                "message" : result.message,
                "bucket_bank" : result.bucket_bank
            }

        else:
            #If the existing question bank is stale or the bank itself is not there yet for the topic provided:
            #Knowledge MCP Server will create a background job and return the relevant information instantly:
            context = {
                "topic" : result.topic_id,
                "status" : InterviewStatus.WAITING_FOR_QS_BANK,
                "job_id" : result.job_id,
                "eta_in_secs" : result.eta_in_secs,
                "message" : result.message

            } 

            #Note: If the question bank is NOT ready and the interview is going to be paused for the generation task to complete,
            #  then the redis update with saving the conversation context NEED to happen in this node ONLY:
            # ResumeState is saved in the redis in the Background Worker already in this case:
            conversation_context.session_memory.interview_status = context["status"]
            print(f"Storing the Conversation Context in Redis for interview id : {interview_id}")
            await self.redis_service.save_interview(user_id=user_id, 
                                                    interview_id=interview_id, 
                                                    context=conversation_context)
        
        #Step 4: Close the MCP Client before returning
        await self.mcp_client.close()

        return  context


    
    
    