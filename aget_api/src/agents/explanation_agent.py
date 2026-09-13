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
from data_models.explanation_agent_llm import ExplanationAgentLLM
from data_models.a2a_response import A2AResponse
from data_models.execution_result import AgentType
from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

openai_api_key = os.getenv("OPENAI_API_KEY")

class ExplanationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, 
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)

        self.name = AgentType.EXPLANATION
        self.description = ("Explains the current interview question by relating the candidate's "
                            "latest answer, evaluation, and previous hints to the authoritative "
                            "reference answer and assessed concepts.")
        self.skills = [AgentSkill.GENERATE_EXPLANATION]
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
                        
        structured_llm = self.llm.with_structured_output(ExplanationAgentLLM)

        chain = prompt | structured_llm

        current_question = context["current_question"]
        candidate_answer = context["candidate_answer"]
        attempt_no = context["attempt_no"]
        evaluation_result = context["evaluation_result"]
        previous_hints = context["previous_hints"]
        reference_answer = context["reference_answer"]
        reference_key_points = context["reference_key_points"]
        primary_concept = context["primary_concept"]
        secondary_concepts = context["secondary_concepts"]

        assembled_keypoints = self.assemble_info(info = reference_key_points)
        assembled_concepts = self.assemble_info(info = [
                                                            [primary_concept],
                                                            secondary_concepts
                                                        ]
                                                )

        rendered_keypoints = self.render_info(info=assembled_keypoints)
        rendered_concepts = self.render_info(info=assembled_concepts)
        

        # --------------------------------------------------
        # Prepare deterministic validation sources
        # --------------------------------------------------

        #-- Not using text to match. Instead using ID to match ----
        # valid_key_points = set(reference_key_points)
        # valid_concepts = set([primary_concept] + secondary_concepts)

        valid_key_points = set(assembled_keypoints.keys())
        valid_concepts = set(assembled_concepts.keys())


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
                                                    "primary_concept" : primary_concept,
                                                    "concepts" : rendered_concepts
                                                }
                                            )


                # --------------------------------------------------
                # Validation 1:
                # Every key point claimed as addressed must
                # exist in the reference key points.
                # --------------------------------------------------

                invalid_key_points  = [kp for kp in output.key_points_addressed if kp not in valid_key_points]

                if invalid_key_points:
                    raise ValueError(f"Explanation contains invalid reference key points: {invalid_key_points}")

                # --------------------------------------------------
                # Validation 2:
                # Every concept claimed as addressed must exist
                # in the question's assessed concepts.
                # --------------------------------------------------
                
                invalid_concepts =[cp for cp in output.concepts_addressed if cp not in valid_concepts]

                if invalid_concepts:
                    raise ValueError(f"Explanation contains unsupported concepts: {invalid_concepts}")


                # --------------------------------------------------
                # Validation 3:
                # Explanation must address the evaluation gaps.
                #
                # This is especially useful when the evaluation
                # identifies missed key points and concepts.
                # --------------------------------------------------

                key_points_missed = evaluation_result.get("key_points_missed",[])
                key_points_missed_IDs = [key for key, val in assembled_keypoints.items() 
                                         if val in key_points_missed]

                concepts_missed = evaluation_result.get("concepts_missed", [])
                concepts_missed_IDs = [key for key, val in assembled_concepts.items() 
                                       if val in concepts_missed]


                if key_points_missed_IDs:
                    missed_points_addressed = set(key_points_missed_IDs) & set(output.key_points_addressed)

                    if key_points_missed_IDs and not missed_points_addressed:
                        raise ValueError("Explanation does not address any of the "
                                            "key points missed in the latest evaluation.")

                    
                if concepts_missed_IDs:
                    missed_concepts_addressed = set(concepts_missed_IDs) & set(output.concepts_addressed)

                    if concepts_missed_IDs and not missed_concepts_addressed:
                        raise ValueError("Explanation does not address any of the "
                                            "concepts  missed in the latest evaluation.")


                # --------------------------------------------------
                # Validation successful
                # --------------------------------------------------    
                print("Explanation Generated Successfully Using LLM ...!")

                #Convert IDs to Text for keypoints and concepts:
                key_points_addressed = [assembled_keypoints.get(i) for i in output.key_points_addressed]
                concepts_addressed = [assembled_concepts.get(i) for i in output.concepts_addressed]
                


                a2a_response = A2AResponse(
                                            agent_name=self.name,
                                            agent_skill=self.skills,
                                            success=True,
                                            event=self.action,
                                            response={
                                                        "data" : {
                                                                    "explanation" : output.explanation  
                                                                }
                                                       },
                                            metadata={
                                                        "key_points_addressed": key_points_addressed,
                                                        "concepts_addressed": concepts_addressed
                                                    }
                                        )
                return a2a_response

                
            except ValueError as exc:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Explanation validation failed:  {exc}")

                if attempt == settings.MAX_RETRIES:
                    raise

                await asyncio.sleep(2 ** attempt)
        
        