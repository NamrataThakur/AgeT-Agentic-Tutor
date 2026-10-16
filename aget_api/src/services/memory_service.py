from datetime import datetime
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from services.redis_service import RedisService
from services.mongodb_service import MongoDBService
from graph.state import AgentState
from data_models.conversation_context import ConversationContext
from data_models.session_memory import SessionMemory, InterviewState, InterviewStatus
from data_models.conversation_message import ConversationMessage
from data_models.execution_result import AgentType
from config.settings import settings
from services.summary_service import SummaryService
from data_models.agent_skills import AgentSkill
from graph.resume_state import ResumeState


class MemoryService:
    def __init__(self, redis_service : RedisService, db_service : MongoDBService,
                                                summary_service : SummaryService):
        
        self.redis_service = redis_service
        self.mongo_service = db_service
        self.summary_service = summary_service


    async def get_or_create_services(self, state : AgentState) -> tuple[ConversationContext, ResumeState | None]:

        #User ID is used to check the MongoDB that stores episodic and procedural memories:
        user_id = state["user_id"] 

        #Interview ID is used to check Redis that stores session memories:
        interview_id = state["interview_id"]


        # ---- If existing interview and resume state is present, then load those ----:
        conversation_context = self.redis_service.get_interview(interview_id=interview_id, 
                                                                user_id=user_id,
                                                                context_model=ConversationContext)
        
        resume_state = self.redis_service.get_resumeState(interview_id=interview_id, 
                                                          user_id=user_id,
                                                          context_model=ResumeState)

        if conversation_context is not None:
            print(f"Conversation Context exists for interview id : {interview_id}")

            print(f"Checking if the interview was paused earlier for interview id : {interview_id}")

            if resume_state is not None:
                print("Interview paused. Resuming the interview now..!") 
                return conversation_context, resume_state
            else:
                print("No paused interview found..!")
                return conversation_context, resume_state


        # ---- If existing interview is NOT present, then create those memories ----:
        print(f"Conversation Context does NOT exists for interview id : {interview_id}")
        print("Creating Memories..!")

        #Note: Resume State does not need to created because there is no history of interview itself, so nothing can be paused (obviously)
        resume_state = None

        interview_status=InterviewStatus.INITIALIZING

        #Create the Session Memory: Redis Connection Exists:
        session_memory = SessionMemory(interview_status=interview_status,
                                       user_id=user_id,
                                       interview_id=interview_id)

    
        #--- To Be used only for local testing in the absence of Redis --- :
        session_memory = await self.mongo_service.get_or_create_session_memory(user_id=user_id, interview_id=interview_id,
                                                                               interview_status=interview_status)

        #Create Episodic Memory:
        episodic_memory = await self.mongo_service.get_or_create_episodic_memory(user_id=user_id, interview_id=interview_id)

        #Create Procedural Memory:
        procedural_memory = await self.mongo_service.get_or_create_procedural_memory(user_id=user_id)

        #Preparing Messages:
        messages = ConversationMessage(
            role="user",
            content=state["user_input"],
            timestamp=datetime.today(),
            turn_id=1,
            agent=None
        )

        print("Memories Created. Building Conversation Context Now..!")


        conversation_context = ConversationContext(
                                    session_memory=session_memory,
                                    episodic_memory=episodic_memory,
                                    procedural_memory=procedural_memory,
                                    knowledge_context=None,
                                    learner_capability_memory=None,
                                    messages=[messages]
                                )

        print(f"Storing the Conversation Context in Redis for interview id : {interview_id}")
        await self.redis_service.save_interview(user_id=user_id, 
                                                interview_id=interview_id, 
                                                context=conversation_context)
        
        return conversation_context, resume_state


    async def save_memories(self, state: AgentState):
        last_qs_id = None

        execution_result = state["execution_result"]
        session_memory = state["conversation_context"].session_memory

        knowledge_context = state["conversation_context"].knowledge_context

        # --------------------------------------------------
        # Update Session Memory
        # --------------------------------------------------
        session_memory.interview_status = InterviewStatus.IN_PROGRESS

        #Step 1: Update Interview State:
        agent_name = execution_result.agent_name
        if agent_name in [AgentType.QUESTION, AgentType.HINT, AgentType.EXPLANATION]:
            interview_state = InterviewState.WAITING_FOR_ANSWER

        elif agent_name == AgentType.EVALUATION:
            interview_state = InterviewState.READY_FOR_NEXT_ACTION

        else:
            raise ValueError(f"Unsupported agent name: {agent_name}")

        session_memory.interview_state = interview_state

        #Step 2: Update Session Memory Fields:
        #Question agent will give the question text, that needs to be updated in the session memory:
        if agent_name == AgentType.QUESTION:
            #Note: If Agent is Question Agent, then execution_result will contain the output of Question Agent.
            #      So, we can directly use it to extract required info.

            #Question Agent will always give new question. So attempt no needs to be set to 1.
            #Assigning attempt no:
            session_memory.attempt_no = 1
            session_memory.hints_given = None

            #Extracting question text:
            session_memory.current_qs = execution_result.response["selected_question"] 

            #Extracting question metadata:
            session_memory.current_qs_metadata = execution_result.metadata["qs_metadata"]

            #Extracting difficulty level:
            session_memory.difficulty = execution_result.metadata["target_difficulty"]

            #Extracting bucket info:
            session_memory.current_bucket = execution_result.metadata["qs_metadata"]["bucket_name"]

            last_qs_id = execution_result.metadata["qs_metadata"]["question_id"]

        #Hint or Explanation Agent doesnot change the question. So atempt no will increase by 1. 
        # Hint Agent's response will be stored in session memory also:
        elif agent_name == AgentType.HINT:
            last_attempt_no = session_memory.attempt_no
            session_memory.attempt_no = last_attempt_no + 1
            current_hint = {"attempt_no" : session_memory.attempt_no,
                           "hint" : execution_result.response["data"]["hint"]
                           }
            all_hints = [] if session_memory.hints_given is None else session_memory.hints_given
            all_hints.append(current_hint)
            session_memory.hints_given = all_hints

        elif agent_name ==  AgentType.EXPLANATION:
            last_attempt_no = session_memory.attempt_no
            session_memory.attempt_no = last_attempt_no + 1

        #Note: Evaluation Agent doesnot change question or attempt counter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 

        #To Be used only for local testing in the absence of Redis:
        #Step 3 : Save session memory to MongoDB: (Optional)
        self.mongo_service.update_session_memory(interview_id=state["interview_id"],
                                                 memory=session_memory)

        # --------------------------------------------------
        # Update Episodic Memory
        # --------------------------------------------------
        episodic_memory = state["conversation_context"].episodic_memory

        #Step 4: Update Episodic Memory:
        #Get all the ids. If first save, then None will come. So need to create the list.
        qs_ids = episodic_memory.questions_asked_ids

        if qs_ids is None:
            qs_ids = []

        #If a new question has come:
        if last_qs_id is not None:
            qs_ids.append(last_qs_id)

            #Update the question id list:
            episodic_memory.questions_asked_ids = qs_ids

            #Update the question attempted count:
            episodic_memory.questions_attempted = len(qs_ids)

        if agent_name == AgentType.EVALUATION:
            score = execution_result.response["score"]
            correctness = execution_result.response["correctness"]

            correct_count = 0 if episodic_memory.questions_correct is None else episodic_memory.questions_correct
            incorrect_count = 0 if episodic_memory.questions_incorrect is None else episodic_memory.questions_incorrect

            if correctness == "correct":
                correct_count = correct_count + 1
                episodic_memory.questions_correct = correct_count
            elif session_memory.attempt_no == settings.MAX_ATTEMPTS:
                incorrect_count= incorrect_count + 1
                episodic_memory.questions_incorrect = incorrect_count

            #If the answer is correct or the user has used up max attempts for this question, 
            # then save the eval results, concept-wise performance etc in episodic memory:
            if correctness == "correct" or session_memory.attempt_no == settings.MAX_ATTEMPTS:
                events = [] if episodic_memory.important_events is None else episodic_memory.important_events
                level_trend = [] if episodic_memory.difficulty_progression is None else episodic_memory.difficulty_progression
                concepts = [] if episodic_memory.concepts_discussed is None else episodic_memory.concepts_discussed

                events.append(execution_result.metadata)
                level_trend.append(session_memory.difficulty)

                concepts = set(concepts)
                concepts.update(set(execution_result.metadata["concepts_demonstrated"]))
                concepts.update(set(execution_result.metadata["concepts_missed"]))
                
                episodic_memory.difficulty_progression = level_trend
                episodic_memory.important_events = events
                episodic_memory.concepts_discussed = list(concepts)

        # --------------------------------------------------
        # Update Procedural Memory - TBD
        # --------------------------------------------------
        procedural_memory = state["conversation_context"].procedural_memory


        # --------------------------------------------------
        # Save Conversation Context → Redis
        # --------------------------------------------------
        conversation_context = ConversationContext(session_memory=session_memory,
                                                    episodic_memory=episodic_memory,
                                                    procedural_memory=procedural_memory,
                                                    knowledge_context=knowledge_context)

        #TO DO: Check: Turn Count can be automatically updated while saving interview in Redis or not
        interview_id = state["interview_id"]
        print(f"Storing the Conversation Context in Redis for interview id : {interview_id}")
        await self.redis_service.save_interview(interview_id=state["interview_id"], 
                                                user_id=state["user_id"], 
                                                context=conversation_context)

        
        # --------------------------------------------------
        # Persist Episodic and Procedural Memory periodically
        # --------------------------------------------------
        #Check the turn_count -> If turn-count >=5:
        #Update Episodic and Procedural Memory Contents in MongoDB:
        if session_memory.turn_count >0 and session_memory.turn_count % settings.MAX_TURN_COUNT == 0:

            #Using all the above info, call LLM to infer the summary field:
            #llm_summary -> will hold summaries for both episodic and procedural memory:
            llm_summary = await self.summary_service.execute(context=conversation_context,
                                                       skill = AgentSkill.SUMMARIZE)
            
            episodic_memory.summary = llm_summary.response["data"]["episodic_summary"]

            #Update the Episodic Memory Collection in MongoDB:
            self.mongo_service.update_episodic_memory(
                interview_id=state["interview_id"],
                user_id =state["user_id"],
                memory=episodic_memory
            )
                
        

        return conversation_context