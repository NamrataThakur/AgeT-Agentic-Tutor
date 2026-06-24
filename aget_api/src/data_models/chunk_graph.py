import json
from pathlib import Path
from typing import List, Literal, Dict

from pydantic import BaseModel, Field


class SemanticChunk(BaseModel):
    """A class representing relations between a pair of chunks.

    Args:
        source_chunk (str): Source Entity Name
        target_chunk (str): Target Entity Name
        shared_entities (List[str]): List of common entities between the source and target chunk
        similarity (float): Weight of the edge between the source and target chunk

    """
    source_chunk : str = Field(description="Source Chunk ID")
    target_chunk : str = Field(description="Target Chunk ID")
    shared_entities: List[str] = Field(description="Common entities")
    similarity : float = Field(ge=0.0, le=1.0)



class SemanticChunkBatch(BaseModel):
    """A class representing all relations present among all the chunks.

    Args:
        semantic_chunk : (List[SemanticChunk]) : list of class SemanticChunk Objects

    """
    semantic_chunk : List[SemanticChunk]