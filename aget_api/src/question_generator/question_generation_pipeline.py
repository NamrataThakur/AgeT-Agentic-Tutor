from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
import networkx as nx
import json
warnings.filterwarnings("ignore")

from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

openai_api_key = os.getenv("OPENAI_API_KEY")

#------------------ STEPS ----------------------------------------------------
#PIPELINE DESCRIPTION ::::: 
#Step 1: Create the retrieval packets for the input topic:
#Step 2: Get the latest knowledge hash from the DB:
#Step 3: Insert the topic packet into the DB:
#Step 4: Get the appropiate prompt considering the difficulty level from the MongoDB:
#Step 5: Render the prompt with input variables:
#Step 6: Call the LLM with structured output:
#Step 7: Validate and post-process the question generated:
#Step 8: Prepare the question metadata for the DB Insertion:
#Step 9: Insert into DB:
#------------------ STEPS ----------------------------------------------------

class QuestionFullGenerationPipeline:
    def __init__(self):
        self.llm = ChatOpenAI(name="gpt-4.1-mini", temperature=0.00, api_key=openai_api_key, max_tokens=1200, max_retries=3)
        self.db = ""
