from collections import defaultdict
import pandas as pd
import json
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.concept_bucket_global import GlobalConcepBucket

class GlobalBucketCreation:
    def __init__(self):
        pass

    async def create_global_bucket(self, topic_id : str, bucket_info: list, question_bank : list) -> GlobalConcepBucket:

        dem_bucket = {
                        buc["bucket_name"] : buc["bucket_id"] 
                        for buc in bucket_info
                    }

        qs_df = pd.DataFrame(question_bank)
        qs_grouped_bucket = qs_df.groupby(["bucket_id","bucket_name", "difficulty"], as_index=False).agg(
                                                                            count=("difficulty", "count"))
        
        bucket_list = []
        for bucket_name, bucket_id in dem_bucket.items():
            print(f"Adding information about bucket : {bucket_name}")

            counts =  {
                        "easy": 0,
                        "medium": 0,
                        "hard": 0
                    }

            df = qs_grouped_bucket[qs_grouped_bucket["bucket_id"] == bucket_id]
                  
            for idx, rows in df.iterrows():
                counts[rows["difficulty"]] = int(rows["count"])

            bucket_info = {
                "bucket_id" : bucket_id,
                "bucket_name" : bucket_name,
                "count" : counts
            }

            bucket_list.append(bucket_info) 

        global_bucket_model = GlobalConcepBucket(
                                                    topic_id=topic_id,
                                                    buckets=bucket_list
                                                )

        return global_bucket_model