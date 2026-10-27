from dotenv import load_dotenv
load_dotenv()
import re
import unicodedata
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
from data_models.question_bank_llm import QuestionGenAllBatch, QuestionGenLLM
from embeddings.embedders import EmbeddingsCreator
from data_models.concept_classification import ConceptClassify
from prompts.concept_classification_prompt import CONCEPT_CLASSIFICATION_SYSTEM_PROMPT, CONCEPT_CLASSIFICATION_USER_PROMPT

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

        self.lookup_dict = {}

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
            
            # ---------- Don't Retry ----------
            except BadRequestError as e:

                print(f"Bad Request: {e}")
                raise   

            # ---------- Retryable ----------
            except Exception as e:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Transient error: {str(e)}")

                if attempt == settings.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)


    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------
    def concept_normalization(self, value: str) -> str:
        if not value:
            return ""

        value = unicodedata.normalize("NFKC", value)

        value = value.lower().strip()

        # Replace separators
        value = value.replace("_", " ")
        value = value.replace("-", " ")

        # Remove punctuation
        value = re.sub(r"[^\w\s]", " ", value)

        # Collapse whitespace
        value = re.sub(r"\s+", " ", value)

        return value.strip()


    def concept_lookup(self, core_concepts: List[str]) -> Dict[str, str]:

        self.lookup_dict = {self.concept_normalization(concept) : concept for concept in core_concepts}
        

    # ---------------------------------------------------------
    # Deterministic validation
    # ---------------------------------------------------------
    def concept_validation(self, generated_concept: str):

        normalized_concept = self.concept_normalization(value=generated_concept)
        validated = self.lookup_dict.get(normalized_concept, None)

        return validated


    def get_top_candidate_concepts(self, concept: str, core_concepts : List[str], top_k : int = 5):
        core_concepts_embedding = np.asarray(self.embedders.get_query_embeddings(query = core_concepts))
        primary_concept_embedding = np.asarray(self.embedders.get_query_embeddings(query=concept))

        # X.shape --> N * 768 (embedding dimension), Y.shape --> 768 (vector). 
        # After Y reshape, Y.shape --> 768 * 1
        # Similarity Matrix shape --> (N*768) X (768*1) = N * 1 (vector)
        similarity_matrix = cosine_similarity(X=core_concepts_embedding, Y=primary_concept_embedding.reshape(1, -1))
        scores = similarity_matrix[:, 0]

        top_indices = np.argsort(scores)[::-1][:top_k]
        top_concepts = [(core_concepts[i], scores[i]) for i in top_indices if scores[i] >= settings.CONCEPT_SIM_THRESHOLD]
        return top_concepts


    def classify_concepts_llm(self, question, primary_concept, secondary_concepts, candidate_concepts) -> ConceptClassify:

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", CONCEPT_CLASSIFICATION_SYSTEM_PROMPT),
                                                        ("user", CONCEPT_CLASSIFICATION_USER_PROMPT)
                                                    ]
                                                )


        structured_llm = self.llm.with_structured_output(ConceptClassify)

        chain = prompt | structured_llm

        for attempt in range(1, settings.MAX_RETRIES + 1):

            try:

                qs_gen_output =  chain.invoke(
                                                {
                                                "question": question.model_dump(),
                                                "primary_concept": primary_concept,
                                                "secondary_concepts" : secondary_concepts,
                                                "candidate_concepts" : candidate_concepts
                                                }
                                            )
                return qs_gen_output

            # ---------- Don't Retry ----------
            except BadRequestError as e:

                print(f"Bad Request: {e}")
                raise
    
            # ---------- Retryable ----------
            except Exception as e:
                print("----------------------------------------------------")
                print(f"[Attempt {attempt}/{settings.MAX_RETRIES}] " 
                        f"Transient error: {str(e)}")

                if attempt == settings.MAX_RETRIES:
                    raise

                time.sleep(2 ** attempt)


    
    def validate_question(self, question : QuestionGenLLM, core_concepts : List[str]) -> QuestionGenLLM | None:

        #Build the look-up dictionary:
        self.concept_lookup(core_concepts=core_concepts)
        
        # -----------------------------------------
        # 1. Try deterministic resolution
        # -----------------------------------------
        primary_resolved = self.concept_validation(generated_concept=question.primary_concept)

        secondary_concepts_validated = []
        for concept in question.secondary_concepts:
            resolved= self.concept_validation(generated_concept=concept)
            if resolved:
                secondary_concepts_validated.append(resolved)
            else:
                secondary_concepts_validated.append(concept)


        # ---------------------------------------------------------------------------------
        # If primary concept is resolved, return the question as validation is complete
        # ---------------------------------------------------------------------------------
        if primary_resolved is not None:
            question.primary_concept = primary_resolved
            question.secondary_concepts = secondary_concepts_validated

            return question


        # -----------------------------------------
        # 2. Primary concept unresolved
        # -----------------------------------------
        candidate_concepts = self.get_top_candidate_concepts(concept=question.primary_concept, 
                                                             core_concepts=core_concepts,
                                                             top_k=5)

        # -----------------------------------------
        # 3. LLM classification
        # -----------------------------------------
        result = self.classify_concepts_llm(question=question, primary_concept=question.primary_concept, 
                                            secondary_concepts=secondary_concepts_validated,
                                            candidate_concepts=candidate_concepts)


        # -----------------------------------------
        # 4. Validate LLM result
        # -----------------------------------------
        if result.primary_concept is None:
            return None

        primary_resolved = self.concept_validation(generated_concept=result.primary_concept)

        if primary_resolved is None:
            return None

        question.primary_concept = primary_resolved

        secondary_resolved = []

        for sec_con in result.secondary_concepts:
            val_sec = self.concept_validation(generated_concept=sec_con)
            if val_sec is not None:
                secondary_resolved.append(val_sec)
            else:
                secondary_resolved.append(sec_con)  

        question.secondary_concepts = secondary_resolved

        return question



    def question_bank_validation(self, core_concepts : List[str], question_bank : QuestionGenAllBatch) -> QuestionGenAllBatch:

        validated_questions = []

        for question in question_bank.question_gen_batch:
            qs = self.validate_question(core_concepts=core_concepts, question=question)

            if qs is not None:
                validated_questions.append(qs)

        validated_questions_model = QuestionGenAllBatch.model_validate(question_gen_batch=validated_questions)
        return validated_questions_model


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


        validated_questions = self.question_bank_validation(core_concepts=topic_info["core_concepts"], 
                                                            question_bank=questions)

        for qs in validated_questions.question_gen_batch:
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

                    # Usage is not tracked here because usage is user specific, whereas question bank is user agnostic
                    # "usage": {"times_asked" : 0, "last_asked_at" : None,
                    #           "correct_count" : 0, "wrong_count" : 0, "average_score" : 0.00
                    #         }
                }
            
            question_bank.append(obj)

        question_bank_with_semantic_clusters = self.create_question_semantic_clusters(questions= question_bank)
            

        print(f"-------------------- QUESTION BANK CREATIED SUCCESSFULLY FOR {difficulty} LEVEL --------------------")
        return question_bank_with_semantic_clusters
    