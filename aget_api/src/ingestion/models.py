import json
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\topics.json", "r") as f:
    topics_data = json.load(f)



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



