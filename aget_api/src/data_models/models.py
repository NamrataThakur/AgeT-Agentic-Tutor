import json
from pathlib import Path
from typing import List, Literal, Dict

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

#Read this url from a config file:
with open(settings.TOPIC_NORMALIZATION_JSON_PATH, "r") as f:
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
                            "coded_by",

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
                            "labels",
                            "has",
                            "generalizes",
                            "extends",
                            "specializes",
                            "equivalent_to",
                            "corresponds_to",
                            "input_of",
                            "output_of",
                            "function_of",
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
        tags (List[str]): Tags of the topic Ex: ['supervised','classification']

    """
    id : str = Field(description = "Unique identifier for the topic")
    name : str = Field(description = "Name of the topic")
    tags : List[str] = Field(description = "Tags of the topic")

    def __str__(self) -> str:
        return f"Topic(id={self.id}, name={self.name}, tags={self.tags})"
    

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
            name=topics_data[id_lower][0],
            tags=topics_data[id_lower][1]

        )
    
    
    @staticmethod
    def get_available_topics() -> List[str]:

        """Returns a list of all available topic IDs.

        Returns:
            list[str]: List of topic IDs that can be instantiated
        """
        return list(topics_data.keys())
    

class RelationType(str, Enum):

    IS_A = "is_a"
    PART_OF = "part_of"
    INSTANCE_OF = "instance_of"
    TYPE_OF = "type_of"
    CAN_BE = "can_be"

    USES = "uses"
    DEPENDS_ON = "depends_on"

    COMPUTED_FROM = "computed_from"
    DERIVED_FROM = "derived_from"

    PARAMETER_OF = "parameter_of"

    CODED_BY = "coded_by"
    ENCODED_USING = "encoded_using"

    CONVERTS = "converts"
    CONVERTED_FROM = "converted_from"
    CONVERTED_TO = "converted_to",
    CONVERTED_BY = "converted_by"

    OUTPUTS = "outputs"
    MAPS_TO = "maps_to"

    MODELS = "models"
    PREDICTS = "predicts"
    ESTIMATES = "estimates"

    OPTIMIZES = "optimizes"
    MINIMIZES = "minimizes"
    MAXIMIZES = "maximizes"

    APPROXIMATES = "approximates"

    DEFINED_AS = "defined_as"
    REPRESENTED_AS = "represented_as",
    REPRESENTS = "represents"

    HAS = "has"
    LABELS = "labels"

    GENERALIZES = "generalizes"
    EXTENDS = "extends"
    SPECIALIZES = "specializes"

    EQUIVALENT_TO = "equivalent_to"
    CORRESPONDS_TO = "corresponds_to"

    INPUT_OF = "input_of"
    OUTPUT_OF = "output_of"
    FUNCTION_OF = "function_of"

    ASSOCIATED_WITH = "associated_with",

    IMPROVES = "improves",
    INCREASES = "increases",
    ASSESSES = "assesses", 
    AFFECTS = "affects"


class OntologyMapping(BaseModel):

    ontology_relation: RelationType


class Relation(BaseModel):
    """A class representing relations to be extracted by LLM from each chunks.

    Args:
        source (str): Source Entity Name
        relation (str): Natural language relation phrase.
        target (str): Target Entity Name
        explanation (str): Short reasoning
        edge_type (str): Type of edge, either 'semantic' or 'contextual'
        confidence (float): Confidence of the edge

    """    
    source : str = Field(description="Source Entity Name")
    relation : str = Field(description="Natural language relation phrase.")
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


class GraphRelation(BaseModel):
    """A class mapping llm extracted relations to ontology from each chunks.

    Args:
        source (str): Source Entity Name
        relation (RelationType): 
        target (str): Target Entity Name
        explanation (str): Short reasoning
        edge_type (str): Type of edge, either 'semantic' or 'contextual'
        confidence (float): Confidence of the edge

    """  
    model_config = ConfigDict(use_enum_values=True)

    source : str = Field(description="Source Entity Name")
    relation: RelationType
    target : str = Field(description="Target Entity Name")
    explanation: str = Field(description="Short reasoning")
    edge_type : str = Field(description="Type of edge, either 'semantic' or 'contextual'")
    confidence : float = Field(ge=0.0, le=1.0)


class GraphRelationBatch(BaseModel):
    """A class representing output of mapping process

    Args:
        relations : (List[GraphRelation]) : list of class GraphRelation Objects

    """
    relations: List[GraphRelation]