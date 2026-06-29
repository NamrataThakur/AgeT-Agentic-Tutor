import json
from pathlib import Path
from typing import List, Literal, Dict

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """A class representing entities present in each each chunks.

    Args:
        text (str): Raw Name of the entity
        normalized_text (str): Normalized Name of the entity
        label (str): Label type
        score (float): score given by gliner model

    """
    text : str = Field(description="Raw Name of the entity")
    normalized_text : str = Field(description="Normalized Name of the entity")
    label : str = Field("Label type")
    score : float = Field(ge=0.0, le=1.0)



class Chunk(BaseModel):
    """A class representing each chunks present in the overall document extracted.

    Args:
        chunk_id (str): Unique Identifier of the chunk
        document_id (str) : Topic ID
        source_id (str) : Source from where topic extracted
        text (str): Raw text present in the chunk
        embedding (List[float]): Embeddings
        entities (List[Entity]): Unique entities present in the chunk

    """
    chunk_id : str = Field(description="Unique Identifier of the chunk")
    document_id : str = Field(description="Topic ID")
    source_id : str = Field(description="Source from where topic extracted")
    text : str = Field(description="Raw text present in the chunk")
    embeddings : List[float]
    entities : List[Entity] 


class ChunkBatch(BaseModel):
    """A class representing all Chunk present in a document.

    Args:
        chunk_batch : (List[Chunk]) : list of class Chunk Objects

    """
    chunk_batch : List[Chunk]