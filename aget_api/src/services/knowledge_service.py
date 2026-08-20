from typing import List, Dict

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.state import AgentState
from services.knowledge_service import KnowledgeService
from db.mongo import MongoDb
from data_models.conversation_context import ConversationContext
from data_models.knowledge_context import KnowledgeContext
from question_generator.question_generation_pipeline import QuestionFullGenerationPipeline

class KnowledgeService:
    def __init__(self):
        self.db = MongoDb()
        self.level = ["easy", "medium", "hard"]
        self.qs_bank_generator = QuestionFullGenerationPipeline()


    async def fetch_qs_bank(self, topic: str) -> List[Dict]:
    
        qs_bank = []

        for lev in self.level:
            print(f"Fetching QS Bank for {lev} questions..!")

            #Find the Highest Prompt Version for the topic and difficulty level chosen:
            cursor_maxVersion = self.db.qs_bank_collection.find_one({
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

                cursor = self.db.qs_bank_collection.find(
                                                        {
                                                            "topic" : topic,
                                                            "difficulty" : lev ,
                                                            "prompt_version" : max_version
                                                        },
                                                        {
                                                            "_id" : 0    
                                                        }
                                                    )
            
                for qs in cursor:
                    qs["created_at"] = str(qs["created_at"])
                    qs_bank.append(qs)


        return qs_bank
    
    async def generate_qs_bank(self, query : str) -> List[Dict]:
        qs_bank, message = self.qs_bank_generator.full_QSBank_generation_pipeline(user_query=query)
        print(message)
        return qs_bank



    async def get_question_bank(self, state : AgentState) -> ConversationContext:
        topic = state["topic"]
        user_input = state["user_input"]

        #Based on this current topic, knowledge service will either load already generated QS Bank
        #  or Generate QS Bank:
        qs_bank = await self.fetch_qs_bank(topic=topic)

        if len(qs_bank) == 0:
            print(f"Question Bank Does Not Exists for the topic : {topic}. Generating Full Question Bank..!")
            qs_bank = await self.generate_qs_bank(query=user_input)



        knowledge_context = KnowledgeContext(topic=topic,
                                            question_bank=qs_bank,
                                            bucket_count=None)

        conversation_context = ConversationContext(knowledge_context=knowledge_context)
        
        return conversation_context