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
from data_models.evaluation_agent_llm import EvaluationAgentLLM
from data_models.a2a_response import A2AResponse
from data_models.execution_result import AgentType
from data_models.agent_skills import AgentSkill
from data_models.execution_plan import Action

openai_api_key = os.getenv("OPENAI_API_KEY")

class EvaluationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, 
                            temperature=settings.MODEL_TEMPERATURE, 
                            api_key=openai_api_key, 
                            max_tokens=settings.MAX_TOKENS,
                            max_retries=settings.MAX_RETRIES)

        self.name = AgentType.EVALUATION
        self.description = ("Selects the next interview question based on candidate performance, "
                            "interview difficulty progression, and eligible candidate questions.")
        self.skills = AgentSkill.EVALUATE_ANSWER
        self.action = Action.EVALUATE


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
        
    
    def validate_evaluation(self, output : EvaluationAgentLLM, concepts : dict, keypoints : dict):

        valid_keyPoints = set(keypoints.keys())
        valid_concepts = set(concepts.keys())

        #Keypoints that LLM gave in "covered" and "missed" sections that are not grounded in Question Bank:
        output_invalid_keypoints_covered = set(output.key_points_covered) - valid_keyPoints
        output_invalid_keypoints_missed = set(output.key_points_missed) - valid_keyPoints

        #Concepts that LLM gave in "demonstrated" and "missed" sections that are not grounded in Question Bank:
        output_invalid_concepts_covered = set(output.concepts_demonstrated) - valid_concepts
        output_invalid_concepts_missed = set(output.concepts_missed) - valid_concepts

        #Keypoints that LLM mentioned them both in "covered" and "missed" sections:
        overlapping_key_points = (set(output.key_points_covered) & set(output.key_points_missed))

        #Concepts that LLM mentioned them both in "demonstrated" and "missed" sections:
        overlapping_concepts = (set(output.concepts_demonstrated) & set(output.concepts_missed))

        errors = []

        if output_invalid_keypoints_covered:
            errors.append(f"Invalid key_points_covered: {list(output_invalid_keypoints_covered)}")

        if output_invalid_keypoints_missed:
            errors.append(f"Invalid key_points_missed: {list(output_invalid_keypoints_missed)}")

        if output_invalid_concepts_covered:
            errors.append(f"Invalid concepts_demonstrated: {list(output_invalid_concepts_covered)}")

        if output_invalid_concepts_missed:
            errors.append(f"Invalid concepts_missed: {list(output_invalid_concepts_missed)}")
        
        if overlapping_key_points:
            errors.append(f"Key points both covered and missed: {overlapping_key_points}")

        if overlapping_concepts:
            errors.append(f"Concepts both demonstrated and missed: {overlapping_concepts}")

        return errors

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
                        
        structured_llm = self.llm.with_structured_output(EvaluationAgentLLM)

        chain = prompt | structured_llm

        session_memory = context["session_context"]

        assembled_keypoints = self.assemble_info(info = [session_memory["key_points"]])
        assembled_concepts = self.assemble_info(info = [
                                                        session_memory["primary_concepts"],
                                                        session_memory["secondary_concepts"]
                                                    ]
                                                )

        rendered_keypoints = self.render_info(info=assembled_keypoints)
        rendered_concepts = self.render_info(info=assembled_concepts)
        
        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                output = await chain.ainvoke(
                                                {
                                                    "current_question": session_memory["last_qs"],
                                                    "user_answer": session_memory["user_input"],
                                                    "reference_answer" : session_memory["ref_answer"],
                                                    "difficulty" : session_memory["current_difficulty"],
                                                    "concepts" : rendered_concepts,
                                                    "primary_concept" : session_memory["primary_concept"],
                                                    "reference_key_points" : rendered_keypoints
                                                }
                                            )

                errors = self.validate_evaluation(output=output, 
                                                  concepts = assembled_concepts,
                                                  keypoints = assembled_keypoints)
                if errors:
                    raise ValueError(f"Evaluation validation failed : {'\n'.join(errors)}")
                
                print("Answer Evaluated Successfully Using LLM ...!")

                #Convert IDs to Text for keypoints and concepts:
                key_points_covered = [assembled_keypoints.get(i) for i in output.key_points_covered]
                key_points_missed = [assembled_keypoints.get(i) for i in output.key_points_missed]

                concepts_demonstrated = [assembled_concepts.get(i) for i in output.concepts_demonstrated]
                concepts_missed = [assembled_concepts.get(i) for i in output.keyconcepts_missed_points_missed]

                a2a_response = A2AResponse(
                                            agent_name=self.name,
                                            agent_skill=self.skills,
                                            success=True,
                                            event=self.action,
                                            response={
                                                        "data" : {
                                                                    "score" : output.overall_score,
                                                                    "correctness" : output.correctness
                                                                }
                                                       },
                                            metadata={  
                                                        "question_id": session_memory["last_qs"],
                                                        "score": output.overall_score,
                                                        "correctness" : output.correctness,
                                                        "primary_concept" : session_memory["primary_concept"],
                                                        "key_points_covered": key_points_covered,
                                                        "key_points_missed": key_points_missed,
                                                        "concepts_demonstrated": concepts_demonstrated,
                                                        "concepts_missed": concepts_missed,
                                                        "misconceptions": output.misconceptions,
                                                        "feedback": output.feedback
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
        
        