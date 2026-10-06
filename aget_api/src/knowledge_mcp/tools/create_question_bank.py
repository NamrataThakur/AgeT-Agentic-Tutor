import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from knowledge_mcp.schema import CreateQSBankRequest, CreateQSBankResponse, QSBankStatus
from services.question_bank_service import QsBankService
from infrastructure.background.job_manager import JobManager
from infrastructure.background.executor import BackgroundExecutor


class CreateQuestionBankTool:
    def __init__(self, qs_service : QsBankService,
                       job_manager : JobManager,
                       executor : BackgroundExecutor):
        
        self.qs_service = qs_service
        self.job_manager = job_manager
        self.background_executor = executor

    async def create_question_bank(self, request: CreateQSBankRequest) -> CreateQSBankResponse:
        """
        Retrieve the latest question bank for a topic. 
            If the question bank is missing, stale, or being regenerated, 
            return the current status and job information.

        Args:
            request (Pydantic object): object of CreateQSBankRequest Pydantic class.

        Returns:
            CreateQSBankResponse: Returns an object of CreateQSBankResponse class.

        """

        #Step 1: Create a job for starting the question bank generation:
        job = await self.job_manager.create_job(topic=request.topic_id, 
                                                task_name="question-generation", 
                                                bucket=None, 
                                                eta_secs=180)


        #Step 2: Submit the job through the background executor:
        await self.background_executor.submit("create_question_bank", 
                                              {
                                                  "user_input" : request.user_input,
                                                  "jobId" : job.get("job_id")
                                              }
                                            )

        #Step 3: It doesnt wait for the execution to complete. 
        # Instead it instantly returns the response:
        return CreateQSBankResponse(topic_id=request.topic_id,
                                    status=QSBankStatus.CREATING,
                                    job_id=job.get("job_id"),
                                    eta_in_secs=job.get("eta_seconds"))

