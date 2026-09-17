from typing import List, Literal, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict



class KnowledgeHash(BaseModel):

    topic : str
    
    sources : dict

    knowledge_hash : str
    
    updated_at : datetime


class KnowledgeHashBatch(BaseModel):
    """A class representing all KnowledgeHash Hashing.

    Args:
        kb_hash_batch : (List[KnowledgeHash]) : list of class KnowledgeHash Objects

    """
    kb_hash_batch : List[KnowledgeHash]

