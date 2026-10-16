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
from bucket_generator.bucket_regeneration_pipeline import BucketRegenerationPipeline
from data_models.concept_bucket_global import GlobalConcepBucket
from bucket_generator.global_bucket_creation import GlobalBucketCreation
from bucket_generator.bucket_health_checker import BucketHealthChecker


class BucketService:
    def __init__(self, db: MongoDb, bucket_creator : GlobalBucketCreation,
                                    bucket_regenerator : BucketRegenerationPipeline,
                                    health_checker : BucketHealthChecker):
        self.db = db
        self.bucket_regenerator = bucket_regenerator
        self.bucket_creator = bucket_creator
        self.health_checker = health_checker

    
    async def fetch_bucket_bank(self, topic:str) -> List[Dict]:
        """
        Fetch the persisted global bucket inventory.
        Bucket details fetch from DB will happen along with fetching the question bank:
        """

        global_bucket_list = []

        cursor = self.db.global_bucket_collection.find_one(
                                                            {
                                                                "topic_id" : topic 
                                                            },
                                                            {
                                                                "_id" : 0,
                                                                "topic_id" : 1,
                                                                "bucket" : 1
                                                            }
                                                        )

        if cursor is None:
            raise ValueError(
                f"No bucket details found for topic='{topic}'."
            )

        global_bucket_list.append(cursor)
        return global_bucket_list

    
    async def bucket_creation(self, topic_id : str, bucket_info: list, question_bank : list) -> GlobalConcepBucket:
        """
        Global Bucket Collection Creation will always happen with question bank creation:
        """
        global_bucket_model = await self.bucket_creator.create_global_bucket(topic_id=topic_id,
                                                                             bucket_info=bucket_info,
                                                                             question_bank=question_bank)
        return global_bucket_model


    async def get_bucket_health(self, bucket_details : Dict):
        """
        Mandatory FIRST step before bucket regeneration. So it can happen 
        either during Question Bank Creation or during maintanence check:
        """

        bucket_health_report = await self.health_checker.get_bucket_health_report(bucket_details=bucket_details)

        return


    #Step 17: If any bucket-level is below threshold, trigger bucket regeneration for them: This will update the Question Bank:
    #Step 18: Check Bucket Health by fetching from DB (again): Validate that all buckets are healthy:
    #Step 19: Return this validated global bucket collection:
    #Step 20: Fetch from DB the latest updated question bank:
    #Step 21: Save Updated Question Bank in local for downstream tasks: 
    async def bucket_regeneration(self, bucket_health):
        """
        Bucket Regeneration can happen either during Question Bank Creation or during maintanence check:
        """
        return
    

    
