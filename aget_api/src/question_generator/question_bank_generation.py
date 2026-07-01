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

#------------------ STEPS ----------------------------------------------------
#PIPELINE DESCRIPTION ::::: 
#Step 5: Render the prompt with input variables: (Done)
#Step 6: Call the LLM with structured output: (Done)
#Step 7: Validate and post-process the question generated: (Done)
#Step 8: Prepare the question metadata for the DB Insertion: (Done)
#------------------ STEPS ----------------------------------------------------

class QuestionGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(name=settings.MODEL_NAME, temperature=settings.MODEL_TEMPERATURE, 
                        api_key=openai_api_key, max_tokens=settings.MAX_TOKENS, max_retries=settings.MAX_RETRIES)


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

            context.append("## Concept Paths (2-Hop)")
            context.append(str(topic_info["concept_paths"]["2_hop"]))
            context.append("")

            context.append("## Retrieved Equations")
            context.append(str(topic_info["retrieved_equations"]))
            context.append("")

        elif difficulty == "hard":
            
            #Apply TOON here to render concept paths:
            
            context.append("## Concept Paths (3-Hop)")
            context.append(str(topic_info["concept_paths"]["3_hop"]))
            context.append("")

            context.append("## Related Relations")
            context.append(str(topic_info["related_relations"]))
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

        qs_gen_output =  chain.invoke(
                                        {
                                        "num_questions": num_questions,
                                        "context": context
                                        }
                                    )

        return qs_gen_output
    

    
    def generate_question_bank(self, prompt : List[dict], topic_info : dict, num_questions : int) -> List[Dict]:
        
        question_bank = []
        system_prompt = prompt[0]["system_prompt"]
        user_prompt = prompt[0]["user_prompt"]
        difficulty = prompt[0]["difficulty"]

        context = self.render_context(topic_info=topic_info, difficulty=difficulty)
        print("-------------------- CONTEXT RENDERED SUCCESSFULLY  --------------------")

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


                    "generator_version" : settings.MODEL_NAME,
                    "created_at" : datetime.today(),
                    "usage": {"times_asked" : 0, "last_asked_at" : None}
                }
            
            question_bank.append(obj)
            

        print(f"-------------------- QUESTION BANK CREATIED SUCCESSFULLY FOR {difficulty} LEVEL --------------------")
        return question_bank
    