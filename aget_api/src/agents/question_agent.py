from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv

load_dotenv()

import os
import sys
from abc import ABC, abstractmethod

os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from agents.base_agent import BaseAgent
from config.settings import settings
from data_models.question_agent_llm import QuestionAgentLLM
from data_models.a2a_response import A2AResponse
from data_models.execution_result import AgentType
from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

openai_api_key = os.getenv("OPENAI_API_KEY")

class QuestionAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, 
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)

        self.name = AgentType.QUESTION
        self.description = ("Selects the next interview question based on candidate performance, "
                            "interview difficulty progression, and eligible candidate questions.")
        self.skills = [AgentSkill.ASK_QUESTION]
        self.action = Action.ASK_QUESTION
    
    async def invoke(self, context, prompt) -> A2AResponse:

        system_prompt = prompt["system_prompt"]
        user_prompt = prompt["user_prompt"]

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", system_prompt),
                                                        ("user", user_prompt)
                                                    ]
                                                )
                        
        structured_llm = self.llm.with_structured_output(QuestionAgentLLM)

        chain = prompt | structured_llm

        session_memory = context["session_context"]
        episodic_memory = context["episodic_context"]
        candidate_questions = context["candidate_questions"]
        target_difficulty = context["target_difficulty"]
        reasoning = context["reasoning"]

        candidate_by_ids = {qs["question_id"] : qs for qs in candidate_questions}

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                output = await chain.ainvoke(
                                                {
                                                    "session_memory": session_memory,
                                                    "episodic_memory": episodic_memory,
                                                    "difficulty_decision" : target_difficulty,
                                                    "candidate_questions" : candidate_questions,
                                                    "difficulty_reasoning" : reasoning
                                                }
                                            )

                selected_qs = candidate_by_ids.get(output.question_id, None)
                if selected_qs is None:
                    raise ValueError(f"LLM selected invalid question_id: {output.question_id}")

                print("Question Selected Successfully Using LLM ...!")

                a2a_response = A2AResponse(
                                            agent_name=self.name,
                                            agent_skill=self.skills,
                                            success=True,
                                            event=self.action,
                                            response={
                                                        "data" : {
                                                                    "selected_question" : selected_qs["question"]  
                                                                }
                                                       },
                                            metadata={
                                                        "reasoning": output.reasoning,
                                                        "target_difficulty": target_difficulty,
                                                        "qs_metadata" : selected_qs
                                                    }
                                        )
                return a2a_response

                
            except ValueError as exc:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"LLM selected invalid question_id : {exc}")

                if attempt == settings.MAX_RETRIES:
                    raise

                await asyncio.sleep(2 ** attempt)
        
        