import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.agent_skills import AgentSkill
from data_models.execution_result import ExecutionResult
from data_models.evaluation_agent_llm import AnswerStatus
from data_models.session_memory import SessionMemory, InterviewState

class PlannerPolicy:
    async def get_allowed_skills(self, session_memory : SessionMemory, execution_result : ExecutionResult | None) -> list[AgentSkill]:

        interview_state = session_memory.interview_state

        if interview_state == InterviewState.INTERVIEW_STARTED:
            return [AgentSkill.ASK_QUESTION]

        if interview_state == InterviewState.WAITING_FOR_ANSWER:
            return [AgentSkill.EVALUATE_ANSWER]

        if interview_state == InterviewState.READY_FOR_NEXT_ACTION:
            #Ready for Next Action can be interview state ONLY AFTER Executor Node has been triggered.
            if execution_result is None:
                raise ValueError("READY_FOR_NEXT_ACTION requires execution_result")

            #Ready for Next Action can be interview state ONLY AFTER evaluation agent has evaluated the last user input:
            if execution_result.agent_skill != AgentSkill.EVALUATE_ANSWER:
                raise ValueError("READY_FOR_NEXT_ACTION requires EvaluationAgent result")

            #Object of AnswerStatus:
            answer_status = execution_result.response["data"]["correctness"] 

            #If last evaluation result is correct, then next action is to ask question
            if answer_status == AnswerStatus.CORRECT:
                return [AgentSkill.ASK_QUESTION]

            #If last evaluation result is incorrect or partially correct, then next action can be giving hint or provide explanation to the user:
            if answer_status in [AnswerStatus.WRONG, AnswerStatus.PARTIALLY_CORRECT]:
                return [AgentSkill.GENERATE_EXPLANATION, AgentSkill.GENERATE_HINT]


        