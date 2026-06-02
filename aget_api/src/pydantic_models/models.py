import json
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field

#Read this url from a config file:
with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\topics.json", "r") as f:
    topics_data = json.load(f)

#Read this url from a config file:
RELATION_TYPES = Literal[

                            # ontology
                            "is_a",
                            "part_of",
                            "instance_of",
                            "type_of",
                            "can_be",

                            # dependency / scientific
                            "uses",
                            "depends_on",
                            "computed_from",
                            "derived_from",
                            "parameter_of",

                            # operational
                            "converts",
                            "converted_from",
                            "converted_to",
                            "outputs",
                            "maps_to",

                            # ML/statistical
                            "models",
                            "predicts",
                            "estimates",
                            "optimizes",
                            "minimizes",
                            "maximizes",
                            "approximates",

                            # equations
                            "parameter_of",
                            "defined_as",
                            "represented_as",

                            # implementation
                            "encoded_using",
                            "labels"
                        ]


class TopicsExtract(BaseModel):
    """A class representing raw data for each topics extracted from external sources.

    This class follows the structure of the data.json file and contains
    basic information about topics before enrichment.

    Args:
        id (str): Unique identifier for the topic.
        urls (List[str]): List of URLs with information about the topic.

    Note: "Topic" here means concepts on which AgeT can interview the user. Example: Logistic Regression, Clustering etc
    """

    id: str = Field(
                        description = "unique identifier for the topic"
                    )
    urls: List[str] = Field(
                                description = "List of URLS with information on the topics"
                            )
    
    @classmethod
    def load_from_json(cls, datafile_path:Path) -> List["TopicsExtract"]:
        with open(datafile_path, "r") as f:
            data_json = json.load(f)
        
        data = [cls(**topic) for topic in data_json]

        return data
    

class Topics(BaseModel):
    """A class representing a topic.

    Args:
        id (str): Unique identifier for the topic.
        name (str): Name of the topic.

    """

    id : str = Field(description = "Unique identifier for the topic")
    name : str = Field(description = "Name of the topic")

    def __str__(self) -> str:
        return f"Topic(id={self.id}, name={self.name})"
    

class TopicsFactory:
    
    @staticmethod
    def get_topic(id: str) -> Topics:
        """Creates a topics instance based on the provided ID.

        Args:
            id (str): Identifier of the topic to create

        Returns:
            Topics: Instance of the topic

        """

        id_lower = id.lower()

        return Topics(
            id=id_lower,
            name=topics_data[id_lower]

        )
    
    
    @staticmethod
    def get_available_topics() -> List[str]:

        """Returns a list of all available topic IDs.

        Returns:
            list[str]: List of topic IDs that can be instantiated
        """
        return list(topics_data.keys())
    


class Relation(BaseModel):
    """A class representing relations to be extracted from each chunks.

    Args:
        source (str): Source Entity Name
        relation (RELATION_TYPES): 
        target (str): Target Entity Name
        explanation (str): Short reasoning
        edge_type (str): Type of edge, either 'semantic' or 'contextual'
        confidence (float): Confidence of the edge

    """
    
    source : str = Field(description="Source Entity Name")
    relation : RELATION_TYPES
    target : str = Field(description="Target Entity Name")
    explanation: str = Field(description="Short reasoning")
    edge_type : str = Field(description="Type of edge, either 'semantic' or 'contextual'")
    confidence : float = Field(ge=0.0, le=1.0)


class RelationExtractBatch(BaseModel):
    """A class representing output of the relation extractor LLM call.

    Args:
        relation : (List[Relation]) : list of class Relation Objects

    """

    relation : List[Relation]




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


class Embeddings(BaseModel):
    """A class representing embeddings of a chunk.

    Args:
        embeddings : (List[float]) : embeddings

    """

    embeddings : List[float]


class Chunk(BaseModel):
    """A class representing each chunks present in the overall document extracted.

    Args:
        chunk_id (str): Unique Identifier of the chunk
        document_id (str) : Topic ID
        text (str): Raw text present in the chunk
        embedding (List[float]): Embeddings
        entities (List[Entity]): Unique entities present in the chunk

    """
    chunk_id : str = Field(description="Unique Identifier of the chunk")
    document_id : str = Field(description="Topic ID")
    text : str = Field(description="Raw text present in the chunk")
    embedding : Embeddings
    entities : List[Entity] 


class ChunkBatch(BaseModel):
    """A class representing all Chunk present in a document.

    Args:
        chunk_batch : (List[Chunk]) : list of class Chunk Objects

    """

    chunk_batch : List[Chunk]


class RelationChunk(BaseModel):
    """A class representing relations to be extracted from each chunks.

    Args:
        source (str): Source Entity Name
        relation (RELATION_TYPES): 
        target (str): Target Entity Name
        explanation (str): Short reasoning
        edge_type (str): Type of edge, either 'semantic' or 'contextual'
        weight (float): Weight of the edge

    """
    
    source : str = Field(description="Source Entity Name")
    relation : RELATION_TYPES
    target : str = Field(description="Target Entity Name")
    explanation: str = Field(description="Short reasoning")
    edge_type : str = Field(description="Type of edge, either 'semantic' or 'contextual'")
    weight : float = Field(ge=0.0, le=1.0)


class RelationBatch(BaseModel):
    """A class representing output of the relation extractor LLM call.

    Args:
        chunk_id (str) : Unique Identifier of the chunk
        relation : (List[Relation]) : list of class Relation Objects

    """

    chunk_id : str = Field(description="Unique Identifier of the chunk")
    relation : List[RelationChunk]
