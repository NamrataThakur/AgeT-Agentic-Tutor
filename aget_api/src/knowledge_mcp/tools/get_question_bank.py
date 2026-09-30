import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from knowledge_mcp.schema import GetQSBankRequest,GetQSBankResponse,QSBankStatus
from services.question_bank_service import QsBankService
from infrastructure.background.job_manager import JobManager
from infrastructure.background.executor import BackgroundExecutor
from infrastructure.background.job_model import BackgroundJob

class GetQuestionBankTool:
    def __init__(self):
        self.qs_service = QsBankService()
        self.job_manager =JobManager()
        self.background_executor = BackgroundExecutor()

    async def get_question_bank(self, request : GetQSBankRequest) -> GetQSBankResponse:
        """
        Retrieve the latest question bank for a topic. 
            If the question bank is missing, stale, or being regenerated, 
            return the current status and job information.

        Args:
            request (Pydantic object): object of GetQSBankRequest Pydantic class.

        Returns:
            GetQSBankResponse: Returns an object of GetQSBankResponse class.
        """

        #This tool will cover 3 scenarios:

        #Step 1: (Common to all scenario): Check if question bank exists:
        existing_qsBank = await self.qs_service.get_qs_bank(topic=request.topic_id)

        # -------------------------------------------------
        # Scenario 1: If Question Bank does not exists for the topic provided:
        # -------------------------------------------------
        #Step 2: Create a job and submit it to the background executor for Question Bank Generation:
        if not existing_qsBank.exists:

            job = BackgroundJob(
                                    topic=request.topic_id,
                                    task_name="question-generation",
                                    bucket=None, 
                                    eta_secs=180
                                )
            
            job = await self.job_manager.create_job(job=job)

            await self.background_executor.submit(
                task_name="create_question_bank",
                payload={
                    "user_input" : request.user_input,
                    "job_id" : job.get("job_id"),
                    "user_id" : request.user_id,
                    "interview_id" : request.interview_id
                }
            )
            return GetQSBankResponse(topic_id=request.topic_id,
                                     status=QSBankStatus.CREATING,
                                     qs_bank=None,
                                     job_id=job.get("job_id"),
                                     eta_in_secs=job.get("eta_seconds"),
                                     message=(
                                                "Question bank isn't available yet. "
                                                "I'm creating it in the background."
                                            )
                                    )
        

        #Scenario 2: If Question Bank exists for the topic, then first check its freshness:
        qs_bank = existing_qsBank.qs_bank
        kn_hashes = existing_qsBank.existing_hash["kn_hash"]

        #Step 3: Get the latest knowledge and prompt hashes stored:
        hashes = await self.qs_service.get_hashes(topic=request.topic_id)
        knowledge_hash = hashes.get("knowledge_hash", "")
        easy_prompt_hash = hashes.get["prompt_hash"]["easy"]
        medium_prompt_hash = hashes.get["prompt_hash"]["medium"]
        hard_prompt_hash = hashes.get["prompt_hash"]["hard"]

        #Checking the freshness by comparing the hashes:
        #If the question bank is fresh, return the bank:
        if (kn_hashes == knowledge_hash 
            and existing_qsBank.existing_hash["easy"] == easy_prompt_hash 
            and existing_qsBank.existing_hash["medium"] == medium_prompt_hash
            and existing_qsBank.existing_hash["hard"] == hard_prompt_hash):

            return GetQSBankResponse(topic_id=request.topic_id,
                                     status=QSBankStatus.READY,
                                     qs_bank=qs_bank,
                                     job_id=None,
                                     eta_in_secs=None,
                                     message="Question Bank is fresh!"
                                     )

        #Scenario 3: If The question bank is stale (i.e. the hashes dont match), then regenerate the question bank:
        job = await self.job_manager.create_job(topic=request.topic_id, 
                                                task_name="question-regeneration", 
                                                bucket=None, 
                                                eta_secs=180)
         
        await self.background_executor.submit(
            "create_question_bank",
            {
                "user_input" : request.user_input,
                "jobId" : job.get("job_id")
            }
        )
        return GetQSBankResponse(topic_id=request.topic_id,
                                status=QSBankStatus.REGENERATING,
                                qs_bank=None,
                                job_id=job.get("job_id"),
                                eta_in_secs=job.get("eta_seconds"),
                                message=(
                                            "The question bank is being refreshed "
                                            "because the underlying knowledge or prompt "
                                            "has changed."
                                        )
                                )

        

