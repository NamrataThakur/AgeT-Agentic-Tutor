

from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graphRag.retriever import Retriever

class LongTermMemoryCustomRetrieval:
    def __init__(self,  db : MongoClient,  model_type = 'openai', k : int= 20, similarity_threshold : float = 0.3):
        self.db = db
        self.ret = Retriever(embed_model_type=model_type, db = self.db)
        self.ret.get_vectorstore()
        self.top_k = k
        
    
    #Vector Retrievals
    def get_vector_retrievals(self, query : str, filter_value : str):

        vector_results = self.ret.vector_store.similarity_search_with_score(query=query, k=self.top_k, 
                                                                            pre_filter={'document_id' : filter_value})
        
        return vector_results
    

    #Vector Rankings based on retrievals:
    def create_vector_rankings(self, vector_results) -> dict:

        vector_rankings = {}

        for rank, (doc, score) in enumerate(vector_results, start=1):
            chunk_id = doc.metadata["chunk_id"]
            obj = {
                'vector_rank' : rank,
                'vector_score' : score,
                'doc' : doc
            }
            vector_rankings[chunk_id] = obj

        return vector_rankings
    

    #BM25 Retrieval
    def get_bm25_retrievals(self, query : str, filter_value : str):

        bm25_pipeline = []

        # 1. Search
        search_pipeline = dict()

        #Since we are pre-filtering based on topic, we need compound query. Constructing parts of the query below:
        filter = [
                    {
                        "equals" :{
                            "path" : "document_id",
                            "value" : filter_value
                        }
                    }
                ]

        must = [
                    {
                        "text": {
                            "query" : query,
                            "path" : [
                                "text",
                                "entities.normalized_text"
                            ]
                        }
                    }
                ]

        search_pipeline["index"] = "text_index"
        search_pipeline["compound"] = {
                                        "filter" : filter,
                                        "must"   : must
                                      }
        bm25_pipeline.append(
                                {
                                    "$search" : search_pipeline
                                }
                            )
        
        # 2. Project fields --> Which fields are required in the metadata part of the output
        project = {
            "chunk_id" : 1,
            "document_id" : 1, 
            "source_id" : 1, 
            "text" : 1,
            "entities" : 1,
            "score" : {
                "$meta" : "searchScore"
            }
        }

        bm25_pipeline.append(
                                {
                                    "$project" : project
                                }
                            )

        # 3. Limit results --> Selecting the top k results based on bm25 score:
        bm25_pipeline.append(
                                {
                                    "$limit" : self.top_k
                                }
                            )
        
        #pipeline now consists of 3 components: search, project, limit --> Query ready to be queried over the collection:
        bm25_results = list(self.db.chunks_collection.aggregate(pipeline=bm25_pipeline))
        return bm25_results
    

    #BM25 Rank based on retrievals:
    def create_bm25_rankings(self, bm25_results) -> dict:

        bm25_rankings = {}

        for rank, doc in enumerate(bm25_results, start=1):
            chunk_id = doc['chunk_id']
            
            obj = {
                "bm25_score" : doc["score"],
                "bm25_rank" : rank,
                "doc" : doc
            }
            bm25_rankings[chunk_id] = obj

        return bm25_rankings
    

    #Weighted Reciprocal Rank Fusion to get hybrid retrievals:
    def weighted_rrf_fusion(self, bm25_rankings : dict, vector_rankings : dict, 
                    vector_weight : float, bm25_weight : float,
                    smoothing_k : int = 60) -> list:

        rrf_scores = defaultdict(float)

        all_chunk_ids = set(vector_rankings.keys()).union(set(bm25_rankings.keys()))

        for chunk_id in all_chunk_ids:
            if chunk_id in vector_rankings:
                rank = vector_rankings[chunk_id]["vector_rank"]
                rrf_scores[chunk_id] += vector_weight * (1 / (smoothing_k + rank))

            if chunk_id in bm25_rankings:
                rank = bm25_rankings[chunk_id]["bm25_rank"]
                rrf_scores[chunk_id] += bm25_weight * (1 / (smoothing_k + rank))

        #Descending order of RRF scores
        rrf_scores = sorted(rrf_scores.items(), key = lambda x: x[1], reverse=True)
        return rrf_scores
    

    #Final hybrid retrieval results:
    def get_rrf_results(self, rrf_scores : list, bm25_rankings : dict, vector_rankings : dict) -> List[Dict]:

        final_fused_results = []

        for rank, (chunk_id, score) in enumerate(rrf_scores, start=1):
            obj = {}
            obj["chunk_id"] = chunk_id
            obj["rrf_score"] = score
            obj["rrf_rank"] = rank
            obj["vector_score"] = vector_rankings.get(chunk_id, {}).get("vector_score")
            obj["vector_rank"] = vector_rankings.get(chunk_id, {}).get("vector_rank")
            obj["bm25_score"] = bm25_rankings.get(chunk_id, {}).get("bm25_score")
            obj["bm25_rank"] = bm25_rankings.get(chunk_id, {}).get("bm25_rank")

            if chunk_id in vector_rankings:
                obj["docs"] = vector_rankings[chunk_id]["doc"]

            elif chunk_id in bm25_rankings:
                obj["docs"] = bm25_rankings[chunk_id]["doc"]


            final_fused_results.append(obj)

        return final_fused_results
    

    #Pipeline covering all the hybrid retrieval steps:
    def custom_retrieval_pipeline(self, query : str, expanded_query : str, 
                                  filter_value : str, vector_weight: float, bm25_weight : float) -> List[Dict]:


        #1. Vector Search on original query
        print("-------------------- VECTOR RETRIEVAL STARTED --------------------")
        vec_res = self.get_vector_retrievals(query=query, filter_value=filter_value)
        vec_ranks = self.create_vector_rankings(vector_results=vec_res)
        print("-------------------- VECTOR RETRIEVAL COMPLETED --------------------")


        #2. BM25 Search on expanded query
        print("-------------------- BM25 RETRIEVAL STARTED --------------------")
        bm25_res = self.get_bm25_retrievals(query=expanded_query, filter_value=filter_value)
        bm25_ranks = self.create_bm25_rankings(bm25_results=bm25_res)
        print("-------------------- BM25 RETRIEVAL COMPLETED --------------------")


        #3. RRF Fusion
        print("-------------------- RRF FUSION STARTED --------------------")
        rrf_fusion_scores = self.weighted_rrf_fusion(bm25_rankings=bm25_ranks, vector_rankings=vec_ranks, 
                                                     vector_weight=vector_weight, bm25_weight=bm25_weight)
        print("-------------------- RRF FUSION COMPLETED --------------------")
        

        #4. RRF results
        final_rrf_res = self.get_rrf_results(rrf_scores=rrf_fusion_scores, bm25_rankings=bm25_ranks, vector_rankings=vec_ranks)

        return final_rrf_res