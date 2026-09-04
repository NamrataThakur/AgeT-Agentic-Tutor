#This file is to be run offline to update/insert prompt for the question agent into the MongoDB.
#During runtime, this prompt will be dynamically loaded.

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


from db.mongo import MongoDb
from data_models.prompt import PromptVersioning
from prompts.hint_prompt import HINT_GENERATION_SYSTEM_PROMPT, HINT_GENERATION_USER_PROMPT


class HintAgentPromptManager:
    def __init__(self):
        self.db = MongoDb()

    def create_hint_agent_prompt(self):
        system_prompt_template = HINT_GENERATION_SYSTEM_PROMPT
        user_prompt_template = HINT_GENERATION_USER_PROMPT

        canonical_prompt, prompt_hash = self.canonicalize_prompts(system_prompt= system_prompt_template,
                                                                  user_prompt= user_prompt_template)
                
        
        prompt_metadata = {
                            "version" : 1,
                            "name" : "HintAgent",
                            "prompt_id": "hint_agent",
                            "created_at" : datetime.today(),
                            "author" : "Namrata Thakur",
                            "status" : "test",
                            "system_prompt" : system_prompt_template,
                            "user_prompt" : user_prompt_template,
                            "prompt_hash" : prompt_hash,
                            "difficulty" : None
                        }
        
        try:

            prompt_versioning_model = PromptVersioning.model_validate(prompt_metadata)
            self.db.ingest_prompt_hash(prompt_hash = [prompt_versioning_model])
            print("Prompt for Question Agent Versioned and Inserted into MongoDB Collection..!")
            
            return  {
                        "system_prompt": system_prompt_template,
                        "user_prompt": user_prompt_template,
                        "prompt_hash": prompt_hash,
                        "prompt_version": 1
                    }
        
        except Exception as e:
            print(f"Exception during Hint Agent's prompt versioning and ingestion : {str(e)}")
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
    prompt_creator = HintAgentPromptManager()
    prompt = prompt_creator.create_hint_agent_prompt()
    print(prompt)

    