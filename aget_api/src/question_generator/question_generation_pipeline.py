from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
import networkx as nx
import json
import time

warnings.filterwarnings("ignore")

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from openai import BadRequestError, RateLimitError, APIConnectionError

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

openai_api_key = os.getenv("OPENAI_API_KEY")


from db.mongo import MongoDb
from graphRag.graph_retrieval_pipeline import GraphRAGPipeline
from config.settings import settings
from data_models.topic_packet import TopicPacket
from data_models.question import QuestionAllBatch
from data_models.concept_bucket_llm import BucketBatch
from question_generator.question_bank_generation import QuestionGenerator
from question_generator.save_question_bank import QuestionBankSave
from prompts.concept_bucket_generation_prompt import CONCEPT_BUCKET_GENERATION_SYSTEM_PROMPT, CONCEPT_BUCKET_GENERATION_USER_PROMPT


#------------------ STEPS ----------------------------------------------------
#PIPELINE DESCRIPTION ::::: 
#Step 1: Create the retrieval packets for the input topic: (Done)
#Step 2: Get the latest knowledge hash from the DB: (Done)
#Step 3: Insert the topic packet into the DB: (Done)
#Step 4: Get the appropiate prompt considering the difficulty level from the MongoDB: (Done)
#Step 5: Render Concept Paths for Representation Compression: (Done)
#Step 6: Render Equations to TOON represented format: (Done)
#Step 7: Render the prompt with input variables: (Done)
#Step 8: Call the LLM with structured output: (Done)
#Step 9: Validate and post-process the question generated: (Done)
#Step 10: Prepare the question metadata for the DB Insertion: (Done)
#Step 11: Entity Bucketing: (Done)
#Step 12: Update QS Bank with Bucket info: (Done)
#Step 13: Insert into DB: (Done)
#STep 14: Save Question Bank in local for downstream tasks: (Done)
#------------------ STEPS ----------------------------------------------------

class QuestionFullGenerationPipeline:
    def __init__(self):

        
        self.db = MongoDb()
        self.mode = "full"

        #Read the parameter values from the settings.py file:
        self.graph_retrieval = GraphRAGPipeline(db = self.db)
        self.qs_generator = QuestionGenerator()
        self.qs_save = QuestionBankSave(db = self.db)
        self.llm = ChatOpenAI(name=settings.MODEL_NAME_QS_GEN, temperature=settings.MODEL_TEMPERATURE, 
                        api_key=openai_api_key, max_tokens=settings.MAX_TOKENS, max_retries=settings.MAX_RETRIES)



    def get_knowledge_hash(self, topic_id : str):

        kb_hash = []

        cursor = self.db.topic_knw_hash_collection.find_one(
                                                                {
                                                                    "topic" : topic_id
                                                                },
                                                                {
                                                                    "_id" : 0,
                                                                    "sources" : 1,
                                                                    "knowledge_hash" : 1
                                                                }
                                                            )

        kb_hash.append(cursor)

        return kb_hash
    

    def get_prompt(self, difficulty: str, status : str) -> List[dict]:

        prompt_hash = []

        cursor = self.db.prompt_hash_collection.find_one(
                                                            {
                                                                "difficulty" : difficulty,
                                                                "status" : status
                                                            },
                                                            {
                                                                "_id" : 0,
                                                                "system_prompt" : 1,
                                                                "user_prompt" : 1,
                                                                "prompt_hash" : 1,
                                                                "difficulty" : 1,
                                                                "prompt_id" : 1,
                                                                "version" : 1
                                                            },
                                                            sort=
                                                                [
                                                                    (
                                                                        "version" , -1
                                                                    )
                                                                ]
                                                        )

        if cursor is None:
            raise ValueError(
                f"No prompt found for difficulty='{difficulty}', status='{status}'"
            )
        
        prompt_hash.append(cursor)

        return prompt_hash
    

    def create_entity_buckets(self, unique_entities: List[str], topic : str) -> List[Dict]:

        prompt = ChatPromptTemplate.from_messages(
                                                    [
                                                        ("system", CONCEPT_BUCKET_GENERATION_SYSTEM_PROMPT),
                                                        ("user", CONCEPT_BUCKET_GENERATION_USER_PROMPT)
                                                    ]
                                                )
        
        structured_llm = self.llm.with_structured_output(BucketBatch)

        chain = prompt | structured_llm

        for attempt in range(1, settings.MAX_RETRIES + 1):
            try:
                bucket_gen_output =  chain.invoke(
                                                {
                                                "topic": topic,
                                                "entities": "\n".join(unique_entities)
                                                }
                                            )
                
                bucket_info = [bucket.model_dump() for bucket in bucket_gen_output.bucket_batch]
                return bucket_info
                
            # ---------- Retryable ----------
            except Exception as e:

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


    def add_qs_buckets(self, questions_bank : List[Dict], bucket_info : List[Dict]) -> List[Dict]:

        #---- Concept -> Bucket Name
        concept_to_bucket = dict()

        for bucket in bucket_info:
            for concept in bucket["primary_concepts"]:
                concept_to_bucket[concept] = bucket["bucket_name"]

            #If the primary concept not found, then use seconday concept
            for concept in bucket["secondary_concepts"]:
                if concept not in concept_to_bucket:
                    concept_to_bucket[concept] = bucket["bucket_name"]
                    
        
        #--- Assign bucket name to each question ----
        for question in questions_bank:
            primary_concept = question["question"]["primary_concept"]
            bucket_name = concept_to_bucket.get(primary_concept, "Uncategorized")
            question["bucket_name"] = bucket_name


        return questions_bank
    
    
    def full_QSBank_generation_pipeline(self, user_query: str ):

        start = time.perf_counter()

        #Step 1: Create the retrieval packets for the input topic: 
        topic_packets = self.graph_retrieval.pipeline(query=user_query, 
                                                      vector_weight=settings.VECTOR_WEIGHT, 
                                                      bm25_weight=settings.BM25_WEIGHT)
        print("Topic Packet Created using the latest Knowledge Hash..!")

        #Step 11: Entity Bucketing:
        entity_buckets = self.create_entity_buckets(unique_entities=list(topic_packets["core_concepts"]), 
                                                    topic = topic_packets["topic_id"])

        #Step 2: Get the latest knowledge hash from the DB:
        kb_hash_info = self.get_knowledge_hash(topic_id=topic_packets["topic_id"])
        knowledge_hash = kb_hash_info[0]["knowledge_hash"]
        print("Latest Knowledge Hash Fetched..!")

        #Step 3: Insert the topic packet into the DB:
        topic_packets["knowledge_hash"] = knowledge_hash
        topic_packets["core_concepts"] = list(topic_packets["core_concepts"])
        topic_packets["supporting_chunks"] = list(topic_packets["supporting_chunks"])
        topic_packets["concept_buckets"] = entity_buckets

        packet_model = TopicPacket.model_validate(topic_packets)
        self.db.ingest_topic_packet(topic_packet=[packet_model])
        print("-------------------- TOPIC PACKET INSERTION IN DB COMPLETED --------------------")


        #Step 4: Get the appropiate prompt considering the difficulty level from the MongoDB:
        easy_prompt = self.get_prompt(difficulty="easy", status="test")
        print(f"Easy Prompt Version Selected : {easy_prompt[0]['version']}")

        medium_prompt = self.get_prompt(difficulty="medium", status="test")
        print(f"Medium Prompt Version Selected : {medium_prompt[0]['version']}")

        hard_prompt = self.get_prompt(difficulty="hard", status="test")
        print(f"Hard Prompt Version Selected : {hard_prompt[0]['version']}")
        print("-------------------- PROMPTS FETCHED FROM DB SUCCESSFULLY  --------------------")

        #Step 5 - 10:
        easy_qsBank = self.qs_generator.generate_question_bank(prompt = easy_prompt, 
                                                          topic_info = topic_packets, 
                                                          num_questions=settings.NUM_QUESTIONS)

        #Step 12: Update QS Bank with Bucket info:
        easy_qsBucket = self.add_qs_buckets(questions_bank=easy_qsBank, bucket_info = entity_buckets)
        print(f"Total EASY Questions Generated : {len(easy_qsBucket)}")

        # #Step 13: Insert into DB:
        easy_qs_model = QuestionAllBatch.model_validate(obj={"question_batch" : easy_qsBucket})
        self.db.ingest_question_bank(qs_bank=easy_qs_model.question_batch)
        print("Question Bank for Easy Questions Inserted in MongoDB Successfully..!")
        print("------------------------------------------------------------------------")

        medium_qsBank = self.qs_generator.generate_question_bank(prompt = medium_prompt, 
                                                            topic_info = topic_packets, 
                                                            num_questions=settings.NUM_QUESTIONS)
        
        # #Step 12: Update QS Bank with Bucket info:
        medium_qsBucket = self.add_qs_buckets(questions_bank=medium_qsBank, bucket_info = entity_buckets)
        print(f"Total MEDIUM Questions Generated : {len(medium_qsBucket)}")

        # #Step 13: Insert into DB:
        medium_qs_model = QuestionAllBatch.model_validate(obj={"question_batch" : medium_qsBucket})
        self.db.ingest_question_bank(qs_bank=medium_qs_model.question_batch)
        print("Question Bank for MEDIUM Questions Inserted in MongoDB Successfully..!")
        print("------------------------------------------------------------------------")

        hard_qsBank = self.qs_generator.generate_question_bank(prompt = hard_prompt, 
                                                          topic_info = topic_packets, 
                                                          num_questions=settings.NUM_QUESTIONS)
        
        # #Step 12: Update QS Bank with Bucket info:
        hard_qsBucket = self.add_qs_buckets(questions_bank=hard_qsBank, bucket_info = entity_buckets)
        print(f"Total HARD Questions Generated : {len(hard_qsBucket)}")

        # #Step 13: Insert into DB:
        hard_qs_model = QuestionAllBatch.model_validate(obj={"question_batch" : hard_qsBucket})
        self.db.ingest_question_bank(qs_bank=hard_qs_model.question_batch)
        print("Question Bank for HARD Questions Inserted in MongoDB Successfully..!")

        print("==================================================================================")


        #STep 14: Save Question Bank in local for downstream tasks:
        self.qs_save.save_qs_bank()

        end = time.perf_counter()
        print(f"Pipeline completed in {end - start:.2f} seconds")

        return "Question Bank Generation Complete..!"
    

if __name__ == "__main__":
    qs_gen = QuestionFullGenerationPipeline()
    res = qs_gen.full_QSBank_generation_pipeline(user_query="ask me on logistic regression")
    print(res)


