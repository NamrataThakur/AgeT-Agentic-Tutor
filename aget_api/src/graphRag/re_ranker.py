from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from langchain_core.documents import Document
import json
import warnings
import re
from rapidfuzz import fuzz

warnings.filterwarnings("ignore")
from sentence_transformers import CrossEncoder

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

class ReRanker:
    def __init__(self, reranker_model_name = "BAAI/bge-reranker-base", k : int = 20) -> list:
        self.reranker = CrossEncoder(model_name_or_path=reranker_model_name)
        self.top_k = k
        

    def get_reranked_chunks(self, query : str, rrf_results : List[Dict]) -> List[Dict]:
        print('--------------- RE-RANKING STARTED -------------------------')

        pairs = []

        for chunk_info in rrf_results:
            if chunk_info["vector_score"] is None:
                doc_content = chunk_info["docs"]["text"]
            else:
                doc_content = chunk_info["docs"].page_content

            pairs.append((query, doc_content))

        
        reranked_scores = self.reranker.predict(pairs)
        ranked_chunks = sorted(zip(rrf_results, reranked_scores), key=lambda x: x[1], reverse=True)[:self.top_k]

        for rank, (doc, score) in enumerate(ranked_chunks, start=1):
            doc["reranked_score"] = score
            doc["reranked_rank"] = rank

        print('--------------- RE-RANKING COMPLETED -------------------------')
        return [doc for doc, score in ranked_chunks]