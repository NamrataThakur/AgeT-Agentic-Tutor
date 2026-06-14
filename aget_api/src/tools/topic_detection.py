from dotenv import load_dotenv
load_dotenv()

from typing import List
from langchain_core.documents import Document
import json
import warnings
import re
from rapidfuzz import fuzz

warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from data_models.models import Topics, TopicsFactory

#Read this url from a config file:
with open(r"D:\LLM_Deeplearning.ai\AgeT-Agentic-Tutor\aget_api\src\data\topics.json", "r") as f:
    topics_data = json.load(f)


class TopicDetection:
    def __init__(self):
        self.topics_data = topics_data
        self.INTENT_PHRASES = [
                                "question", "ask", "quiz",
                                "test", "give",
                                "topics","covering","me",
                                "on ", "about "
                            ]
        

    def get_topic(self, query : str) -> tuple[List[Topics] | List[str] , str]:

        normalized_query = self.normalize_query(query=query)
        
        topic_list = []

        if normalized_query in set(self.topics_data.keys()):
            topic = TopicsFactory().get_topic(normalized_query)
            topic_list.append(topic)
            message = "Topic Found in Knowledge Base."

        else:
            for k, v in self.topics_data.items():
                if normalized_query == self.normalize_query(query=v[0]):
                    topic = TopicsFactory().get_topic(id = k)
                    topic_list.append(topic)
                    message = "Topic Found in Knowledge Base."
                    break

                elif any(tag in normalized_query for tag in v[1] ):
                    topic = TopicsFactory().get_topic(id = k)
                    topic_list.append(topic)
                    message = "Topic Found in Knowledge Base."
                
                
        if len(topic_list) == 0:
            print("No topic detection yet. Trying Fuzzy Match..!")
            #Fuzzy Match Fallback:
            for k,v in self.topics_data.items():
                if any([fuzz.partial_ratio(tag, normalized_query) > 60 
                        for tag in v[1] ]):
                    topic = TopicsFactory().get_topic(id = k)
                    topic_list.append(topic)
                    message = "Topic Found in Knowledge Base."
            
        if len(topic_list) == 0:
            print("Fuzzy Match Failed..!")
            topic = TopicsFactory.get_available_topics()
            topic_list.extend(topic)
            message = "Topic NOT Found in Knowledge Base..!"

        return (topic_list, message)


    def normalize_query(self, query : str) -> str:

        q = query.lower().strip()

        #Replace "-", "_" with space. Ex: log-reg --> log reg, log_reg --> log reg
        q = re.sub(r"[-_]+", " ", q)

        #Fuzzy Matching on the Sample Intent Phases:
        for phase in self.INTENT_PHRASES:
            if fuzz.partial_ratio(phase, q) > 50:
                q = q.replace(phase, "")

        normalized_query = " ".join(q.split())
        return normalized_query



if __name__ == '__main__':
    topic_ext = TopicDetection()
    topic, message = topic_ext.get_topic(query="ask me on neural network")
    print(topic)
    print(message)