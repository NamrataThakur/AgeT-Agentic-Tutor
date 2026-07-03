from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
import networkx as nx
import json
import time

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

from db.mongo import MongoDb
from config.settings import settings


class QuestionBankSave:
    def __init__(self, db : MongoClient):
        self.db = db

    def save_qs_bank(self):

        qs_bank = []

        cursor = self.db.qs_bank_collection.find(   
                                                    {},
                                                    {
                                                        "_id" : 0,
                                                        "topic" : 1,
                                                        "question" : 1,
                                                        "difficulty" : 1,
                                                        "generator_version" : 1,
                                                        "created_at" : 1,
                                                        "prompt_version" : 1,
                                                        "bucket_name" : 1, 
                                                        "prompt_id" : 1
                                                    }
                                                )
        
        for qs in cursor:
            qs["created_at"] = str(qs["created_at"])
            qs_bank.append(qs)

        file_path = settings.INTERMITTENT_DATA / "Question_Bank.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(qs_bank, f, indent=4)


if __name__ == "__main__":
    db = MongoDb()
    qs_bank = QuestionBankSave(db=db)
    qs_bank.save_qs_bank()
