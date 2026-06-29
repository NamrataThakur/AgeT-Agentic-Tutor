#File contains logic to create source hash and overall knowledge hash for a particular topic:

from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from pymongo import MongoClient
import warnings
import json
import hashlib
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
from data_models.knowledge_hash import KnowledgeHashBatch


class KnowledgeHashCreator:
    def __init__(self, db: MongoClient):
        self.db = db

    def get_hashing_data(self, source_name : str, topic_name : str) -> List[Dict]:

        cursor = self.db.chunks_collection.find(
                                                    {
                                                        "source_id" : source_name,
                                                        "document_id" : topic_name
                                                    },
                                                    {
                                                        "_id" : 0,
                                                        "chunk_id" : 1,
                                                        "document_id" : 1, 
                                                        "source_id" : 1,
                                                        "text" : 1,
                                                        "entities" : 1
                                                    }
                                                )
        

        hashing_data = list(cursor)
        return hashing_data
    

    def create_source_hash(self, source_data : List[Dict])  -> str:

        payload = []

        for chunk in sorted(source_data, key=lambda x:x["chunk_id"], reverse=False):
            obj = {
                "chunk_id" : chunk["chunk_id"],
                "document_id" : chunk["document_id"],
                "source_id" : chunk["source_id"],
                "text" : chunk["text"],
                "entities" : chunk["entities"]
            }
            payload.append(obj)

        canonical_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=("," , ":"))
        hash_info = hashlib.sha256(string=canonical_json.encode("utf-8")).hexdigest()

        return hash_info
    

    def create_knowledge_hash(self, source_hashes : Dict) -> str:

        canonical_json = json.dumps(source_hashes, sort_keys=True, ensure_ascii=False, separators=("," , ":"))
        hash_info = hashlib.sha256(string=canonical_json.encode("utf-8")).hexdigest()

        return hash_info
    

    def knowledge_hashing_pipeline(self, source_name : List[str], topic_name : List[str]):
        
        all_topic = []

        for topic in topic_name:
            knowledge_hash_data = dict()

            topic_hash = dict()
            topic_hash["topic"] = topic

            for source in source_name:

                #Step 1: Get the data for hashing:
                hashing_data = self.get_hashing_data(source_name=source, topic_name=topic)

                #Step 2: Create the source hash:
                source_hash = self.create_source_hash(source_data=hashing_data)

                #Create a payload for knowledge hashing using all source hashes:
                knowledge_hash_data[source] = source_hash
                                                
            #Step 3: Create a combined knowledge hash:
            knowledge_hash = self.create_knowledge_hash(source_hashes=knowledge_hash_data)

            topic_hash["sources"] = knowledge_hash_data
            topic_hash["knowledge_hash"] = knowledge_hash
            topic_hash["updated_at"] = datetime.today()

            all_topic.append(topic_hash)

        return all_topic
    

if __name__ == "__main__":
    db = MongoDb()
    hash_obj = KnowledgeHashCreator(db=db)
    hashes = hash_obj.knowledge_hashing_pipeline(source_name=["Wikipedia"], topic_name=["logistic_regression"])
    hash_model = KnowledgeHashBatch.model_validate(obj={"kb_hash_batch" : hashes})

    db.ingest_knowledge_hash(knw_hash=hash_model.kb_hash_batch)
    
    print(hashes)

    