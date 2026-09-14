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
from data_models.hint_agent_llm import HintAgentLLM
from data_models.a2a_response import A2AResponse
from data_models.execution_result import AgentType
from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

openai_api_key = os.getenv("OPENAI_API_KEY")

class HintAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, 
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)

        self.name = AgentType.HINT
        self.description = ("Generates a progressively targeted hint for the current interview "
                            "question based on the candidate's latest answer, evaluation, "
                            "missed key points, and previously provided hints.")
        self.skills = [AgentSkill.GENERATE_HINT]
        self.action = Action.GENERATE


    def assemble_info(self, info : list) -> dict:
        assembled_info = {}

        if len(info) == 1:
            for i, val in enumerate(info[0], start=1): #Keypoints in list
                assembled_info[f"KP{i}"] = val 

        else:
            assembled_info["C1"] = info[0] #Primary Concept in string
            for i, val in enumerate(info[1], start=2): #Secondary Concept in list
                assembled_info[f"C{i}"] = val

        return assembled_info
    
    
    def render_info(self, info : dict):
        rendered_output = []
        for key, val in info.items():
            rendered_output.append(f"[{key}] : {val}")

        print("-------------------- INFORMATION REPRESENTED in TOON SUCCESSFULLY  --------------------")   
        return "\n".join(rendered_output)

    
    async def invoke(self, context, prompt) -> A2AResponse:

        system_prompt = prompt["system_prompt"]
        user_prompt = prompt["user_prompt"]

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", system_prompt),
                                                        ("user", user_prompt)
                                                    ]
                                                )
                        
        structured_llm = self.llm.with_structured_output(HintAgentLLM)

        chain = prompt | structured_llm

        current_question = context["current_question"]
        candidate_answer = context["candidate_answer"]
        attempt_no = context["attempt_no"]
        evaluation_result = context["evaluation_result"]
        previous_hints = context["previous_hints"]
        reference_answer = context["reference_answer"]
        reference_key_points = context["reference_key_points"]
        secondary_concepts = context["secondary_concepts"]
        primary_concept = context["primary_concept"]

        kp_missed = context["evaluation_result"]["key_points_missed"]

        assembled_keypoints = self.assemble_info(info = reference_key_points)
        assembled_concepts = self.assemble_info(info = [
                                                            [primary_concept],
                                                            secondary_concepts
                                                        ]
                                                )
        assembled_keypoints_missed = self.assemble_info(info=kp_missed)

        rendered_keypoints = self.render_info(info=assembled_keypoints)
        rendered_concepts = self.render_info(info=assembled_concepts)
        rendered_keypoints_missed = self.render_info(info=assembled_keypoints_missed)

        # --------------------------------------------------
        # Prepare deterministic validation sources
        # --------------------------------------------------

        key_points_missed = evaluation_result.get("key_points_missed",[])
        key_points_missed_IDs = [key for key, val in assembled_keypoints.items() 
                                                 if val in key_points_missed]


        #If Evaluation Agent didnt flag any keypoint to be missed, then Hint Agent shouldn't be called. 
        # Because Hint Agent is designed to give hints based on the keypoints missed.
        #Note: HANDLE THIS IN PLANNER TOO AND IN THE MIDDLEWARE GUARDRAIL
        if not key_points_missed_IDs:
            raise ValueError("Hint Agent was invoked but the evaluation contains "
                                "no missed key points."
                            )

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                output = await chain.ainvoke(
                                                {
                                                    "current_question": current_question,
                                                    "candidate_answer": candidate_answer,
                                                    "attempt_no" : attempt_no,
                                                    "evaluation_result" : evaluation_result,
                                                    "previous_hints" : previous_hints,
                                                    "reference_answer": reference_answer,
                                                    "reference_key_points" : rendered_keypoints,
                                                    "key_points_missed" : rendered_keypoints_missed,
                                                    "primary_concept" : primary_concept,
                                                    "concepts" : rendered_concepts,
                                                }
                                            )

                print("Hint Generated Successfully Using LLM ...!")

                if output.target_key_point not in key_points_missed_IDs:
                    raise ValueError(f"Hint generated is not grounded." 
                                     f"Generated target_key_point is not present in "
                                     f"evaluation.key_points_missed: {output.target_key_point}")
                
                print("Generated Hint is grounded in the knowledge context ...!")

                #Convert IDs to Text for keypoints and concepts:
                target_key_point = assembled_keypoints[output.target_key_point]

                a2a_response = A2AResponse(
                                            agent_name=self.name,
                                            agent_skill=self.skills,
                                            success=True,
                                            event=self.action,
                                            response={
                                                        "data" : {
                                                                    "hint" : output.hint
                                                                }
                                                        },
                                            metadata={
                                                        "target_key_point" : target_key_point
                                                    }
                                        )
                return a2a_response

            except ValueError as exc:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Hint grounding validation failed : {exc}")

                if attempt == settings.MAX_RETRIES:
                    raise

                await asyncio.sleep(2 ** attempt)

                
            
        
        