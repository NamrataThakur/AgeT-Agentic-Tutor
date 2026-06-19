
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

class ChunkExpander:
    def __init__(self, db : MongoClient, top_k : int = 5, expanded_chunk_length : int = 15):
        self.db = db

       #How many seed chunks:
        self.top_k = top_k

        #How many total neighbours: Final chunk expansion results = seed chunk + total neighbours
        self.expanded_chunk_length = expanded_chunk_length


    def get_neighbours(self, chunk : Dict) -> List[Dict]:

        chunk_id = chunk["chunk_id"]

        neighbours = []

        #This returns all chunks where the conditions are met:
        cursor = self.db.chunk_edges_collection.find(
                                                        {
                                                            "$or" : [
                                                                {
                                                                    "Source_chunk" : chunk_id
                                                                },
                                                                {
                                                                    "target_chunk" : chunk_id
                                                                }
                                                            ]
                                                        }

                                                    )
        
        #Extract the chunk details for each of the neighbour chunks:
        for res in cursor:
            if res["source_chunk"] == chunk_id:
                chunk_info = self.single_chunk_details(chunk_id=res["target_chunk"])[0]["chunk_id"]
                neighbours.append({"chunk" :chunk_info, "similarity" :res["similarity"]})

            elif res["target_chunk"] == chunk_id:
                chunk_info = self.single_chunk_details(chunk_id=res["source_chunk"])[0]["chunk_id"]
                neighbours.append({"chunk" :chunk_info, "similarity" :res["similarity"]})

        return neighbours


    def single_chunk_details(self, chunk_id : str) -> List[Dict]:

        chunk_info = []

        #We need only chunk_id from this query:
        cursor = self.db.chunks_collection.find_one(
                                                    {
                                                        "chunk_id" : chunk_id
                                                    },
                                                    {
                                                        "_id": 0,
                                                        "chunk_id": 1
                                                    }      
                                                    )
        

        chunk_info.append(cursor)   

        return chunk_info
    

    def multi_chunk_details(self, chunk_id : List[str]) -> List[Dict]:

        chunk_info = []

        cursor = self.db.chunks_collection.find(
                                                    {
                                                        "chunk_id" : {
                                                            "$in" : chunk_id
                                                        }
                                                    },
                                                    {
                                                        "_id": 0,
                                                        "chunk_id": 1,
                                                        "text": 1,
                                                        "entities": 1,
                                                        "document_id": 1,
                                                        "source_id": 1
                                                    }  
                                                         
                                                    )
        
        for res in cursor:
            chunk_info.append(res)   

        return chunk_info
    

    def chunk_expansion_pipeline(self, reranked_chunks : List[Dict]) -> List[Dict] :
        print('--------------- CHUNK EXPANSION STARTED -------------------------')

        chunk_expansion_results = {}

        seed_chunks = reranked_chunks[:self.top_k]
        seed_chunk_ids = set([seed["chunk_id"] for seed in seed_chunks])

        for seed in seed_chunks:
            
            #Take all the neighbours of each seed chunks:
            neighbours = self.get_neighbours(chunk=seed)

            #For each seed chunk, score each neighbour using seed chunk's reranker score and neighbour's edge weight:
            for neighbour in neighbours:
                
                neigh_chunk_id = neighbour["chunk"]
                if neigh_chunk_id in seed_chunk_ids:
                    continue

                score = neighbour["similarity"] * seed["reranked_score"]
                
                #Deduplication across all seed chunks:
                chunk_expansion_results[neigh_chunk_id] = max(score, chunk_expansion_results.get(neigh_chunk_id, 0))

        #Select top 'N' unique neighbour chunks across all seed chunks:        
        #This contains top 'N' neighbours' chunk_id
        expanded_chunks = sorted(chunk_expansion_results.items(), key=lambda x : x[1], reverse=True)[:self.expanded_chunk_length]
        
        expanded_chunks_id = [chunkid for chunkid, score in expanded_chunks]
        

        #Get the complete chunk details for these 'N' chunk:   
        expanded_chunks_info = self.multi_chunk_details(expanded_chunks_id)

        #Add the expansion score and rank:
        for rank, (chunkid, score) in enumerate(expanded_chunks, start=1):
            for d in expanded_chunks_info:
                if d["chunk_id"] == chunkid:
                    d["expansion_score"] = score
                    d["expansion_rank"] = rank

        expanded_chunks_info = sorted(expanded_chunks_info, key=lambda x: x["expansion_score"], reverse=True)

        #Total chunks : seed + top neighbours --> Chunk Expansion complete
        final_expanded_results = seed_chunks + expanded_chunks_info

        print('--------------- CHUNK EXPANSION COMPLETED -------------------------')
        return final_expanded_results
    



