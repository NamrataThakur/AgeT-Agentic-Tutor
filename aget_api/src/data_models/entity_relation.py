import json
from pathlib import Path
from typing import List, Literal, Dict

from pydantic import BaseModel, Field


class RelationChunk(BaseModel):
    """A class representing relations to be inserted to mongodb.

    Args:
        source (str): Source Entity Name
        relation (RELATION_TYPES): 
        target (str): Target Entity Name
        explanation (str): Short reasoning
        edge_type (str): Type of edge, either 'semantic' or 'contextual'
        weight (float): Weight of the edge

    """    
    source : str = Field(description="Source Entity Name")
    relation : str = Field(description="Relation type")
    target : str = Field(description="Target Entity Name")
    explanation: str = Field(description="Short reasoning")
    edge_type : str = Field(description="Type of edge, either 'semantic' or 'contextual'")
    weight : float = Field(ge=0.0, le=1.0)


class RelationSingleBatch(BaseModel):
    """A class representing all relations present in a chunk.

    Args:
        chunk_id (str) : Unique Identifier of the chunk
        relation : (List[Relation]) : list of class Relation Objects

    """
    chunk_id : str = Field(description="Unique Identifier of the chunk")
    relation : List[RelationChunk]


class RelationAllBatch(BaseModel):
    """A class representing all relations present in all chunk.

    Args:
        relation_batch : List[RelationSingleBatch]

    """
    relation_batch : List[RelationSingleBatch]