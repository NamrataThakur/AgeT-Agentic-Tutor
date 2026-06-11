#The graphRag pipeline starts here:
from dotenv import load_dotenv
load_dotenv()
import warnings

warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from typing import List, Literal
from tools.topic_detection import TopicDetection
from data_models.models import Topics
from graphRag.retriever import Retriever
from memory.long_term_memory_retrieval import LongTermMemoryRetrieval

#TO DO :
# ================================================== RAG BEGINS ================================
# 1. Input Query --> TopicDetection (Done)
# 2. TopicDetection --> List of Topics (Done)
# 3. Get the topic_id of each of those topics --> Pre-filtering using topic_id as metadata
# 4. Hybrid retrieval using RRF --> Top 20 chunks
# 5. Re-ranking of results using Re-ranker to get top 10 chunks
# =================================================== RAG ENDS ==================================
# =============================== GRAPH EXPANSION BEGINS ==================================

# =============================== GRAPH EXPANSION ENDS ==================================

class GraphRAGPipeline:
    def __init__(self, model_type : str = "openai", top_k : int = 20, similarity_threshold : float = 0.3):
        self.topic_detector = TopicDetection()
        self.retriever = LongTermMemoryRetrieval(model_type=model_type, k=top_k, similarity_threshold= similarity_threshold )


    def pipeline(self, query : str):

        extracted_topics, message = self.topic_detector.get_topic(query=query)
        topic_list = []

        if message == "Topic NOT Found in Knowledge Base..!":

            return extracted_topics, message
        
        #TO DO: IF more than one topic is detected, clarify with user which one to select --> TO be done during Agent implementation
        
        #For now, use all topics detected:
        for topic in extracted_topics:
            topic_list.append(topic.id)

        
        



