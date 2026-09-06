from typing import List, Literal, Dict, Set

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PathEdge(BaseModel):
    """A class representing relations present in each path.

    Args:
        source (str): Source Entity Name
        relation (str): Relation
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


class TwoHopPath(BaseModel):
    """A class representing Two Hop Paths present within Concept Paths.

    Args:
        path (List[PathEdge]): 2-hop paths 
        path_score (float): Overall Score of this 2-hop Path
        path_quality (str) : Description of the path quality. Options: 'weak' or 'strong'

    """ 

    path : List[PathEdge] = Field(min_length=2, max_length=2)
    path_score : float
    path_quality : str = Field(description="Path quality. Options: 'weak' and 'strong'. ")


class ThreeHopPath(BaseModel):
    """A class representing Three Hop Paths present within Concept Paths.

    Args:
        path (List[PathEdge]): 3-hop paths 
        path_score (float): Overall Score of this 3-hop Path
        path_quality (str) : Description of the path quality. Options: 'weak' or 'strong'

    """ 

    path : List[PathEdge] = Field(min_length=3, max_length=3)
    path_score : float
    path_quality : str = Field(description="Path quality. Options: 'weak' and 'strong'. ")


class ConceptPaths(BaseModel):
    """A class representing Concept Paths.

    Args:
        two_hop (Dict[str, List[TwoHopPath]]): All the 2-hop paths extracted from the supporting chunks
        three_hop (Dict[str, List[ThreeHopPath]]): All the 3-hop paths extracted from the supporting chunks

    """ 

    two_hop : Dict[str, List[TwoHopPath]] = Field(alias="2_hop")
    three_hop : Dict[str, List[ThreeHopPath]] = Field(alias="3_hop")
    
    model_config = {
        "populate_by_name": True
    }


class TopicPacket(BaseModel):
    """A class representing final topic packet.

    Args:
        topic_id (str): Unique ID of the topic
        knowledge_hash (str): Hash value of the KB used to create this packet
        core_concepts (Set[str]): Unique Entities present in the supporting chunks
        supporting_chunks (Set[str]): Text of the supporting chunks
        concept_paths (ConceptPaths)
        retrieved_equations (List[Dict]): Equation paths having 'mentions' relations
        related_equations (List[Dict]): Equation paths having 'co_occurs' relations
        concept_buckets (List[Dict]): Semantic buckets used during assessment rounds
        
    """ 

    topic_id : str = Field(description="Unique ID of the topic")
    knowledge_hash : str = Field(description="Hash value of the KB used to create this packet")
    core_concepts : List[str] = Field(description="Unique Entities present in the supporting chunks")
    supporting_chunks : List[str] = Field(description="Text of the supporting chunks")
    concept_paths : ConceptPaths
    retrieved_equations : List[Dict] = Field(description="Equation paths having 'mentions' relations")
    related_equations : List[Dict] = Field(description="Equation paths having 'co_occurs' relations")
    concept_buckets : List[Dict] = Field(description="Semantic buckets used during assessment rounds")