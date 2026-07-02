from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
import json
import hashlib
import re
from datetime import datetime

warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from prompts.easy_question_generation_prompt import EASY_QUESTION_GENERATION_SYSTEM_PROMPT, EASY_QUESTION_GENERATION_USER_PROMPT
from prompts.medium_question_generation_prompt import MEDIUM_QUESTION_GENERATION_SYSTEM_PROMPT, MEDIUM_QUESTION_GENERATION_USER_PROMPT
from prompts.hard_question_generation_prompt import HARD_QUESTION_GENERATION_SYSTEM_PROMPT, HARD_QUESTION_GENERATION_USER_PROMPT
from data_models.prompt import PromptVersioning
from db.mongo import MongoDb

#------------------ STEPS ----------------------------------------------------
#Step 1: Get the system and user prompt template: (Done)
#Step 2: Add the input variables to the template according to the 'mode': (Done)
#Step 3: Canonicalize prompt template: (Done)
#Step 4: Create the hash: (Done)
#Step 5: Prepare the prompt metadata for the DB Insertion: (Done)
#Step 6: Insert into DB: (Done)
#------------------ STEPS ----------------------------------------------------


class PromptCreator:
    def __init__(self):
        self.db = MongoDb()


    def create_easyQs_prompt(self):
        
        system_prompt_template = EASY_QUESTION_GENERATION_SYSTEM_PROMPT
        user_prompt_template = EASY_QUESTION_GENERATION_USER_PROMPT

        
        # else:
        #    input_variables = {
        #                         "required": [
        #                             "unique_entities",
        #                             "supporting_chunks",
        #                             "num_questions",
        #                             "bucket_name",
        #                             "primary_concepts",
        #                             "secondary_concepts"
        #                         ]
        #                     }
            
        
        canonical_prompt, prompt_hash = self.canonicalize_prompts(system_prompt= system_prompt_template,
                                                                  user_prompt= user_prompt_template)
        

        prompt_metadata = {
                            "version" : 4,
                            "name" : "Easy Question Prompt",
                            "prompt_id": "easy_question_generation",
                            "created_at" : datetime.today(),
                            "author" : "Namrata Thakur",
                            "status" : "test",
                            "system_prompt" : system_prompt_template,
                            "user_prompt" : user_prompt_template,
                            "prompt_hash" : prompt_hash,
                            "difficulty" : "easy"
                        }
        
        try:

            prompt_versioning_model = PromptVersioning.model_validate(prompt_metadata)
            self.db.ingest_prompt_hash(prompt_hash = [prompt_versioning_model])
            print("Prompt Versioned and Inserted into MongoDB Collection..!")
            
            return  {
                        "system_prompt": system_prompt_template,
                        "user_prompt": user_prompt_template,
                        "prompt_hash": prompt_hash,
                        "prompt_version": 4,
                        "difficulty" : "easy"
                    }
        
        except Exception as e:
            print(f"Exception during prompt versioning and ingestion : {str(e)}")
            raise
        


    
    def create_mediumQs_prompt(self):

        system_prompt_template = MEDIUM_QUESTION_GENERATION_SYSTEM_PROMPT
        user_prompt_template = MEDIUM_QUESTION_GENERATION_USER_PROMPT

        # else:
        #    input_variables = {
        #                         "required": [
        #                             "unique_entities",
        #                             "supporting_chunks",
        #                             "num_questions",
        #                             "concept_paths",
        #                             "retrieved_equations",
        #                             "bucket_name",
        #                             "primary_concepts",
        #                             "secondary_concepts"
        #                         ]
        #                     }
            
        
        canonical_prompt, prompt_hash = self.canonicalize_prompts(system_prompt= system_prompt_template,
                                                                  user_prompt= user_prompt_template)
        

        prompt_metadata = {
                            "version" : 3,
                            "name" : "Medium Question Prompt",
                            "prompt_id": "medium_question_generation",
                            "created_at" : datetime.today(),
                            "author" : "Namrata Thakur",
                            "status" : "test",
                            "system_prompt" : system_prompt_template,
                            "user_prompt" : user_prompt_template,
                            "prompt_hash" : prompt_hash,
                            "difficulty" : "medium"
                        }
        
        try:

            prompt_versioning_model = PromptVersioning.model_validate(prompt_metadata)
            self.db.ingest_prompt_hash(prompt_hash = [prompt_versioning_model])
            print("Prompt Versioned and Inserted into MongoDB Collection..!")
            
            return  {
                        "system_prompt": system_prompt_template,
                        "user_prompt": user_prompt_template,
                        "prompt_hash": prompt_hash,
                        "prompt_version": 3,
                        "difficulty" : "medium"
                    }
        
        except Exception as e:
            print(f"Exception during prompt versioning and ingestion : {str(e)}")
            raise
    
    def create_hardQs_prompt(self):

        system_prompt_template = HARD_QUESTION_GENERATION_SYSTEM_PROMPT
        user_prompt_template = HARD_QUESTION_GENERATION_USER_PROMPT

        
        # else:
        #    input_variables = {
        #                         "required": [
        #                             "unique_entities",
        #                             "supporting_chunks",
        #                             "num_questions",
        #                             "concept_paths",
        #                             "related_relations",
        #                             "bucket_name",
        #                             "primary_concepts",
        #                             "secondary_concepts"
        #                         ]
        #                     }
            
        
        canonical_prompt, prompt_hash = self.canonicalize_prompts(system_prompt= system_prompt_template,
                                                                  user_prompt= user_prompt_template)
        

        prompt_metadata = {
                            "version" : 1,
                            "name" : "Hard Question Prompt",
                            "prompt_id": "hard_question_generation",
                            "created_at" : datetime.today(),
                            "author" : "Namrata Thakur",
                            "status" : "test",
                            "system_prompt" : system_prompt_template,
                            "user_prompt" : user_prompt_template,
                            "prompt_hash" : prompt_hash,
                            "difficulty" : "hard"
                        }
        
        try:

            prompt_versioning_model = PromptVersioning.model_validate(prompt_metadata)
            self.db.ingest_prompt_hash(prompt_hash = [prompt_versioning_model])
            print("Prompt Versioned and Inserted into MongoDB Collection..!")
            
            return  {
                        "system_prompt": system_prompt_template,
                        "user_prompt": user_prompt_template,
                        "prompt_hash": prompt_hash,
                        "prompt_version": 1,
                        "difficulty" : "hard"
                    }
        
        except Exception as e:
            print(f"Exception during prompt versioning and ingestion : {str(e)}")
            raise
    

    def canonicalize_prompts(self, system_prompt : str, user_prompt : str) -> tuple[str, str]:
        
        # Normalize line endings
        system_prompt = system_prompt.replace("\r\n", "\n").replace("\r", "\n")
        user_prompt = user_prompt.replace("\r\n", "\n").replace("\r", "\n")

        # Remove trailing whitespace from every line
        system_prompt = "\n".join(line.rstrip() for line in system_prompt.split("\n"))
        user_prompt = "\n".join(line.rstrip() for line in user_prompt.split("\n"))

        # Collapse 3+ blank lines into 2
        system_prompt = re.sub(r"\n{3,}", "\n\n", system_prompt)
        user_prompt = re.sub(r"\n{3,}", "\n\n", user_prompt)

        # Strip leading/trailing whitespace
        system_prompt = system_prompt.strip()
        user_prompt = user_prompt.strip()


        canonical = json.dumps(
                                {
                                    "system_prompt": system_prompt,
                                    "user_prompt": user_prompt
                                },
                                sort_keys=True,
                                separators=(",", ":"),
                                ensure_ascii=False,
                            )

        prompt_hash = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        return canonical, prompt_hash
    

if __name__ == "__main__":
    prompt_creator = PromptCreator()
    # easy_prompt = prompt_creator.create_easyQs_prompt()
    medium_prompt = prompt_creator.create_mediumQs_prompt()
    # hard_prompt = prompt_creator.create_hardQs_prompt()