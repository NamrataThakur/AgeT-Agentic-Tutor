import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.execution_result import AgentType
from pymongo import MongoClient

class PromptService:
    def __init__(self,db : MongoClient):
        self.db = db

    def load_prompt(self, agent_name : str, status : str, summary : bool) -> dict:

        projection = {
                        "_id": 0,
                        "system_prompt": 1,
                        "user_prompt": 1,
                        "prompt_hash": 1,
                        "prompt_id": 1,
                        "version": 1,
                        "name" : 1
                    }


        if summary:
            #We would need to load two prompts under "summary" --> for episodic summary and procedural summary.
            #So, we will need to load the latest version for each prompts separately:
            
            prompt = {}
            # --------------------------------------------------
            # Step 1: Get unique prompt IDs
            # --------------------------------------------------
            prompt_ids = self.db.prompt_hash_collection.distinct(
                                                                    "prompt_id",
                                                                    {
                                                                        "name" : agent_name,
                                                                        "status" : status
                                                                    }
                                                                )
            # Keep ordering deterministic
            prompt_ids = sorted(prompt_ids)

            # --------------------------------------------------
            # Step 2: Get latest version for each prompt ID
            # --------------------------------------------------
            for prompt_id  in prompt_ids:
                cursor = self.db.prompt_hash_collection.find_one(
                                                                    {
                                                                        "name" : agent_name,
                                                                        "status" : status,
                                                                        "prompt_id" : prompt_id 

                                                                    },
                                                                    projection,
                                                                    sort=
                                                                        [
                                                                            (
                                                                                "version" , -1
                                                                            )
                                                                        ]
                                                                    )

                if cursor is not None:
                    prompt[prompt_id] = cursor

        else:
            #Find the Highest Prompt Version for the Agent Name given:
            prompt = self.db.prompt_hash_collection.find_one(
                                                                {
                                                                    "name" : agent_name,
                                                                    "status" : status
                                                                },
                                                                projection,
                                                                sort=
                                                                    [
                                                                        (
                                                                            "version" , -1
                                                                        )
                                                                    ]
                                                                )

            
        if not prompt:
            raise ValueError(
                f"No prompt found for Agent='{agent_name}', status='{status}'"
            )

        return prompt