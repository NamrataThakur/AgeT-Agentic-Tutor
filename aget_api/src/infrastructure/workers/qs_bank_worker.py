#This file handles the background task co-ordination. It checks 

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from infrastructure.background.job_manager import JobManager
from services.question_bank_service import QsBankService
from services.redis_service import RedisService
from graph.resume_state import ResumeState
from services.redis_event_service import RedisEventService


class QsBankWorker:
    def __init__(self, question_service : QsBankService, 
                       job_manager : JobManager,
                       redis_service : RedisService,
                       event_service : RedisEventService):
        
        self.qs_service = question_service
        self.job_manager = job_manager
        self.redis_service = redis_service
        self.event_service = event_service


    async def qsbank_worker_execute(self, user_input: str, job_id : str, interview_id: str, user_id : str):

        try:
            #Step 1: Update the Job Status to "running":
            await self.job_manager.mark_running(job_id=job_id)

            #Step 2: Create the resume state with status as "Waiting":
            obj = {
                    "waiting_job_id" : job_id,
                    "status" : "WAITING",
                    "pause_reason" : f"Job ({job_id}) is waiting to start."
                }
            
            resume_model = ResumeState.model_validate(obj)
            
            await self.redis_service.save_resumeState(interview_id=interview_id,
                                                      user_id=user_id,
                                                      context= resume_model)

            #Step 3: Start the Question Bank Generation Pipeline:
            result = await self.qs_service.create_qs_bank(user_input=user_input)

            #Step 4: Update the Job Status if execution is completed successfull:
            await self.job_manager.mark_ready(job_id=job_id, result = result.model_dump())

            #Step 5: Update the resume state with status as "Ready":
            obj = {
                    "waiting_job_id" : job_id,
                    "status" : "READY",
                    "pause_reason" : f"Job ({job_id}) completed. Question Bank Ready"
                }
            
            resume_model = ResumeState.model_validate(obj)
            
            await self.redis_service.save_resumeState(interview_id=interview_id,
                                                        user_id=user_id,
                                                        context= resume_model )
            
            #Step 6: Publish the event to the UI:
            event_id = await self.event_service.publish_events(
                event_type="job.completed",
                job_id=job_id,
                job_type="qsBank_generation",
                user_id=user_id,
                interview_id=interview_id,
                payload={
                    "user_input" : user_input,
                    "result" : result.message
                }
            )


        except Exception as e:

            #Step 6: Update the job status if exception is raised:
            await self.job_manager.mark_failed(job_id=job_id, error=str(e))

            #Step 7: Update the resume state with status as "Failed":
            obj = {
                    "waiting_job_id" : job_id,
                    "status" : "FAILED",
                    "pause_reason" : f"Job ({job_id}) failed.",
                    "error" : str(e)
                }
            
            resume_model = ResumeState.model_validate(obj)

            await self.redis_service.save_resumeState(interview_id=interview_id,
                                                        user_id=user_id,
                                                        context= resume_model)

            #Step 6: Publish the event to the UI:
            event_id = await self.event_service.publish_events(
                event_type="job.failed",
                job_id=job_id,
                job_type="qsBank_generation",
                user_id=user_id,
                interview_id=interview_id,
                payload={
                    "user_input" : user_input,
                    "error" : str(e)
                }
            )

            raise