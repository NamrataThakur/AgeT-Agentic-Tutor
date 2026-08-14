import os
import sys
from datetime import datetime
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.mongo import MongoDb
from data_models.episodic_memory import EpisodicMemory
from data_models.procedural_memory import ProceduralMemory
from data_models.session_memory import SessionMemory


class MongoDBService:
    def __init__(self):
        self.db = MongoDb()


    async def get_or_create_episodic_memory(self, user_id : str, interview_id : str) -> EpisodicMemory:

        #Checking if the User Exists in Episodic Memory Collection of MongoDB:
        episodic_docs = self.db.episodic_memory_collection.find_one(
                                                                    {
                                                                        "user_id" : user_id
                                                                    },
                                                                    {
                                                                        "_id" : 0
                                                                    }
                                                                )


        #If User Exists, then return the memory after Pydantic Validation:
        if episodic_docs is not None:
            memory = EpisodicMemory.model_validate(episodic_docs)
            print("Episodic Memory Loaded From MongoDB..!")
            return memory


        #If User DOES NOT Exists, Create Pydantic Object for the memory:
        memory = EpisodicMemory(user_id=user_id,
                                interview_id=interview_id,
                                started_at=datetime.today())


        #Update the MongoDB Collection:
        self.db.ingest_memory(memory_type="episodic", memory=[memory])

        return memory

    async def get_or_create_procedural_memory(self, user_id : str) -> ProceduralMemory:

        #Checking if the User Exists in Procedural Memory Collection of MongoDB:
        procedural_docs = self.db.procedural_memory_collection.find_one(
                                                                    {
                                                                        "user_id" : user_id
                                                                    },
                                                                    {
                                                                        "_id" : 0
                                                                    }
                                                                )


        #If User Exists, then return the memory after Pydantic Validation:
        if procedural_docs is not None:
            memory = ProceduralMemory.model_validate(procedural_docs)
            print("Procedural Memory Loaded From MongoDB..!")
            return memory
        

        #If User DOES NOT Exists, Create Pydantic Object for the memory:
        memory = ProceduralMemory(user_id=user_id,
                                  started_at=datetime.today())


        #Update the MongoDB Collection:
        self.db.ingest_memory(memory_type="procedural", memory=[memory])

        return memory

    #To Be used only for local testing in the absence of Redis:
    async def get_or_create_session_memory(self, interview_id : str) -> SessionMemory:
    
        #Checking if the User Exists in Session Memory Collection of MongoDB:
        session_docs = self.db.temp_session_memory_collection.find_one(
                                                                    {
                                                                        "interview_id" : interview_id
                                                                    },
                                                                    {
                                                                        "_id" : 0
                                                                    }
                                                                )


        #If User Exists, then return the memory after Pydantic Validation:
        if session_docs is not None:
            memory = SessionMemory.model_validate(session_docs)
            print("Session Memory Loaded From MongoDB..!")
            return memory
        

        #If User DOES NOT Exists, Create Pydantic Object for the memory:
        memory = SessionMemory(interview_id=interview_id,
                                interview_status="interview_started")


        #Update the MongoDB Collection:
        self.db.ingest_memory(memory_type="session", memory=[memory])

        return memory
