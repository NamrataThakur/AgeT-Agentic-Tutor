from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
import networkx as nx
import json
from datetime import datetime
import uuid
import time
import numpy as np
from openai import BadRequestError, RateLimitError, APIConnectionError
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings("ignore")

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

openai_api_key = os.getenv("OPENAI_API_KEY")

from config.settings import settings
from data_models.question_bank_llm import QuestionGenAllBatch
from embeddings.embedders import EmbeddingsCreator

#------------------ STEPS ----------------------------------------------------
#PIPELINE DESCRIPTION ::::: 
#Step 5: Render Concept Paths for Representation Compression: (Done)
#Step 6: Render Equations to TOON represented format: (Done)
#Step 7: Render the prompt with input variables: (Done)
#Step 8: Call the LLM with structured output: (Done)
#Step 9: Validate and post-process the question generated: (Done)
#Step 10: Prepare the question metadata for the DB Insertion: (Done)
#------------------ STEPS ----------------------------------------------------

class QuestionGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, temperature=settings.MODEL_TEMPERATURE, 
                        api_key=openai_api_key, max_tokens=settings.MAX_TOKENS, max_retries=settings.MAX_RETRIES)
        self.embedders = EmbeddingsCreator(embed_model_type=settings.MODEL_TYPE)

    def render_paths(self, concept_paths : Dict) -> str:

        rendered_output = []

        quality_map = {
                            "strong" : "s",
                            "weak" : "w"
                        }

        for entity, path_info in concept_paths.items():
            for path in path_info:

                quality = quality_map.get(
                                            path.get("path_quality"), "not_available"
                                        )
                score = path.get("path_score", 0)

                chain = path["path"][0]["source"]
                for edge in path["path"]:
                    chain += f"- {edge['relation']} -> {edge['target']}"

                rendered_output.append(f"[{quality}|{score:.4f}] {chain}")

        print("-------------------- REPRESENTATION COMPRESSION COMPLETED SUCCESSFULLY  --------------------")
        return "\n".join(rendered_output)

    
    def render_equations(self, equation_paths: List[dict]) -> str:

        if len(equation_paths) == 0:
            return "None"
        
        rendered_output = []

        for eq in equation_paths:
            equation = eq["target"]
            text = eq["source"]

            rendered_output.append(f"[EQ] {equation} \n INTUITION: {text}")

        print("-------------------- EQUATION REPRESENTED in TOON SUCCESSFULLY  --------------------")
        return "\n".join(rendered_output)


    def render_context(self, topic_info : dict, difficulty : str):

        context = []

        # ---------------------------------------------------
        # Common Context
        # ---------------------------------------------------

        context.append("## Available Entities")
        context.append(str(topic_info["core_concepts"]))
        context.append("")

        context.append("## Supporting Knowledge")
        context.append(str(topic_info["supporting_chunks"]))
        context.append("")

        # ---------------------------------------------------
        # Difficulty Specific Context
        # ---------------------------------------------------

        if difficulty == "medium":
            
            #Apply TOON here to render concept paths:
            rendered_paths = self.render_paths(concept_paths=topic_info["concept_paths"]["2_hop"])
            rendered_equations = self.render_equations(equation_paths=topic_info["retrieved_equations"])

            context.append("## Concept Paths (2-Hop)")
            #context.append(str(topic_info["concept_paths"]["2_hop"]))
            context.append(rendered_paths)
            context.append("")

            context.append("## Retrieved Equations")
            #context.append(str(topic_info["retrieved_equations"]))
            context.append(rendered_equations)
            context.append("")

        elif difficulty == "hard":
            
            #Apply TOON here to render concept paths:
            rendered_paths = self.render_paths(concept_paths=topic_info["concept_paths"]["3_hop"])
            rendered_equations = self.render_equations(equation_paths=topic_info["related_equations"])

            context.append("## Concept Paths (3-Hop)")
            #context.append(str(topic_info["concept_paths"]["3_hop"]))
            context.append(rendered_paths)
            context.append("")

            context.append("## Related Equations")
            #context.append(str(topic_info["related_equations"]))
            context.append(rendered_equations)
            context.append("")

        return "\n".join(context)
    
    

    def generate_questions(self, system_prompt : str, user_prompt : str, context : str, num_questions : int) -> QuestionGenAllBatch:

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", system_prompt),
                                                        ("user", user_prompt)
                                                    ]
                                                )


        structured_llm = self.llm.with_structured_output(QuestionGenAllBatch)

        chain = prompt | structured_llm

        for attempt in range(1, settings.MAX_RETRIES + 1):

            try:

                qs_gen_output =  chain.invoke(
                                                {
                                                "num_questions": num_questions,
                                                "context": context
                                                }
                                            )
                return qs_gen_output
                
            # ---------- Retryable ----------
            except Exception as e:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Transient error: {str(e)}")

                if attempt == settings.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)

            # ---------- Don't Retry ----------
            except BadRequestError as e:

                print(f"Bad Request: {e}")
                raise

            except Exception as e:

                print(f"Unexpected Exception: {e}")
                raise

        

    def create_question_semantic_clusters(self, questions: List[Dict]) -> List[Dict]:

        question_text = [qs["question"]["question"] for qs in questions]

        question_bank_embedding = np.asarray(self.embedders.get_query_embeddings(query = question_text))

        similarity_matrix = cosine_similarity(question_bank_embedding)
        
        sim_n = len(questions)

        for i in range(sim_n):

            neighbours = []

            for j in range(sim_n):

                if i == j:
                    continue
                
                score = similarity_matrix[i][j]
                if score >= settings.QUESTION_SIM_THRESHOLD:
                    neighbours.append(
                        {
                            "question_id" : questions[j]["question_id"],
                            "similarity" : round(float(score), 3)
                        }
                    )
            
            neighbours = sorted(neighbours, key=lambda x: x["similarity"], reverse=True)
            questions[i]["semantic_neighbours"] = neighbours

        return questions
        

    
    def generate_question_bank(self, prompt : List[dict], topic_info : dict, num_questions : int) -> List[Dict]:
        
        question_bank = []
        system_prompt = prompt[0]["system_prompt"]
        user_prompt = prompt[0]["user_prompt"]
        difficulty = prompt[0]["difficulty"]

        context = self.render_context(topic_info=topic_info, difficulty=difficulty)
        print(f"-------------------- CONTEXT RENDERED SUCCESSFULLY FOR {difficulty} LEVEL --------------------")

        print(f"-------------------- QUESTION BANK GENERATION STARTED FOR {difficulty} LEVEL --------------------")
        questions = self.generate_questions(system_prompt=system_prompt, 
                                            user_prompt=user_prompt,
                                            context=context,
                                            num_questions=num_questions )


        for qs in questions.question_gen_batch:
            obj = {
                    "topic" : topic_info["topic_id"],
                    "knowledge_hash" : topic_info["knowledge_hash"],
                    "prompt_hash" : prompt[0]["prompt_hash"],
                    "prompt_id" : prompt[0]["prompt_id"],
                    "prompt_version" : prompt[0]["version"],

                    "question_id" : str(uuid.uuid4()),
                    "question" : qs.model_dump(),
                    "difficulty" : difficulty,


                    "generator_version" : settings.MODEL_NAME_QS_GEN,
                    "created_at" : datetime.today(),
                    "usage": {"times_asked" : 0, "last_asked_at" : None,
                              "correct_count" : 0, "wrong_count" : 0, "average_score" : 0.00
                            }
                }
            
            question_bank.append(obj)

        question_bank_with_semantic_clusters = self.create_question_semantic_clusters(questions= question_bank)
            

        print(f"-------------------- QUESTION BANK CREATIED SUCCESSFULLY FOR {difficulty} LEVEL --------------------")
        return question_bank_with_semantic_clusters
    