from typing import List, Literal, Dict
from pydantic import BaseModel, Field

class Bucket(BaseModel):
    """
    A class representing semantic buckets used during assessment rounds.
    
    Args:
        bucket_id (str) : Unique Id for each bucket
        bucket_name (str): Semantic name of the bucket
        description (str): Description of the bucket
        primary_concepts (List[str]): Primary Concept List
        secondary_concepts (List[str]): Secondary Concept List
    
    """ 
    bucket_id : str = Field(description="Unique Id of the bucket")
    bucket_name : str = Field(description="Semantic name of the bucket")
    easy_qs_count : int = Field(default=0, description="Count of Easy Questions")
    medium_qs_count : int = Field(default=0,description="Count of Medium Questions")
    hard_qs_count : int  = Field(default=0,description="Count of Hard Questions")


class GlobalConcepBucket(BaseModel):
    """A class representing all buckets present across a particular topic.

    Args:
        topic_id (str): Topic Id for the buckets
        bucket_batch (List[Bucket]): List of Bucket objects

    """  
    topic_id : str = Field(description="Topic id for the bucket")
    buckets : List[Bucket]
    