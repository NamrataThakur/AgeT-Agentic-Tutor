from dataclasses import dataclass
from typing import List, Dict, Any
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.mongo import MongoDb
from question_generator.question_generation_pipeline import QuestionFullGenerationPipeline


@dataclass
class QsBankState:
    exists : bool
    qs_bank : List[Dict] | None
    existing_hash : Dict | None


class QsBankService:
    def __init__(self):
        self.db = MongoDb()
        self.qs_bank_generator = QuestionFullGenerationPipeline()

    async def fetch_qs_bank(self, topic: str) -> tuple[List[Dict], Dict]:
        
        qs_bank = []
        prompt_kn_hashes = {}

        for lev in self.level:
            print(f"Fetching QS Bank for {lev} questions..!")

            #Find the Highest Prompt Version for the topic and difficulty level chosen:
            cursor_maxVersion = await self.db.qs_bank_collection.find_one(
                                                    {
                                                        "topic" : topic,
                                                        "difficulty" : lev 
                                                    },
                                                    {
                                                        "_id" : 0,
                                                        "prompt_version": 1
                                                    },
                                                    sort=
                                                        [
                                                            (
                                                                "prompt_version" , -1
                                                            )
                                                        ]
                                                    )
            
            #Now find all questions having the highest prompt version:
            if cursor_maxVersion:
                max_version = cursor_maxVersion["prompt_version"]

                cursor = await self.db.qs_bank_collection.find(
                                                        {
                                                            "topic" : topic,
                                                            "difficulty" : lev ,
                                                            "prompt_version" : max_version
                                                        },
                                                        {
                                                            "_id" : 0    
                                                        }
                                                    )
                prompt_hashes = set()
                kn_hashes = set()

                for qs in cursor:
                    qs["created_at"] = str(qs["created_at"])
                    prompt_hashes.add(qs["prompt_hash"])
                    kn_hashes.add(qs["knowledge_hash"])
                    qs_bank.append(qs)

                prompt_kn_hashes[lev] = prompt_hashes
                prompt_kn_hashes["kn_hash"] = kn_hashes

        return qs_bank, prompt_kn_hashes

    
    async def get_qs_bank(self, topic: str) -> QsBankState:

        #Based on this current topic, question bank service will load already generated QS Bank:
        qs_bank, prompt_kn_hashes = await self.fetch_qs_bank(topic=topic)

        if len(qs_bank) == 0:
            print(f"Question Bank Does Not Exists for the topic : {topic}. Generating Full Question Bank..!")
            return QsBankState(exists=False, 
                               qs_bank=None,
                               existing_hash=None)


        return QsBankState(exists=True, 
                           qs_bank=qs_bank, 
                           existing_hash=prompt_kn_hashes)

    
    async def get_hashes(self, topic : str) -> dict:

        hashes = {}
        prompts = {}

        topic_cursor = await self.db.topic_knw_hash_collection.find_one(
                                                            {
                                                                "topic" : topic
                                                            },
                                                            {
                                                                "_id" : 0,
                                                                "knowledge_hash" : 1,
                                                                "updated_at" : 1
                                                            },
                                                            sort=
                                                            [
                                                                (
                                                                    "updated_at" , -1 
                                                                )
                                                            ]
                                                            )

        if topic_cursor is not None:
            hashes["knowledge_hash"] = topic_cursor["knowledge_hash"]
        else:
            hashes["knowledge_hash"] = None

        
        for lev in self.level:
            print(f"Fetching Prompt Hash for {lev} questions..!")

            #Find the Highest Prompt Version for the difficulty level chosen:
            cursor_prompt = await self.db.prompt_hash_collection.find_one(
                                                    {
                                                        "difficulty" : lev 
                                                    },
                                                    {
                                                        "_id" : 0,
                                                        "prompt_id": 1,
                                                        "prompt_hash" : 1,
                                                        "version" : 1
                                                    },
                                                    sort=
                                                        [
                                                            (
                                                                "version" , -1
                                                            )
                                                        ]
                                                    )
            if cursor_prompt is not None:
                prompts[lev] = cursor_prompt["prompt_hash"]
            else:
                prompts[lev] = None

        hashes["prompt_hash"] = prompts

        return hashes
            
    

    async def create_qs_bank(self, user_input:str) -> QsBankState:
        qs_bank, message, hashes = self.qs_bank_generator.full_QSBank_generation_pipeline(user_query=user_input)
        print(message)
        return QsBankState(exists=True, 
                           qs_bank=qs_bank,
                           existing_hash=hashes)