import json
from pathlib import Path
from typing import List, Literal, Dict

from pydantic import BaseModel, Field


class ConceptBucket(BaseModel):
    """A class representing semantic buckets used during assessment rounds.

    Args:
        bucket_name (str): Semantic name of the bucket
        description (str): Description of the bucket
        primary_concepts (List[str]): Primary Concept List
        secondary_concepts (List[str]): Secondary Concept List

    """  

    bucket_name : str = Field(description="Semantic name of the bucket")
    description : str = Field(description="One-line description of the interview topic covered by this bucket.")
    primary_concepts : List[str] = Field(min_length=4, max_length=6, 
                                         description="Concepts that should become the primary concept during question generation.")
    secondary_concepts : List[str] = Field(min_length=2, max_length=6,
                                           description="Supporting concepts that may appear in the generated questions but should not be selected as primary concepts.")



class BucketBatch(BaseModel):
    """A class representing all buckets present across all entities.

    Args:
        bucket_batch (List[ConceptBucket]): List of ConceptBucket objects

    """  

    bucket_batch : List[ConceptBucket]