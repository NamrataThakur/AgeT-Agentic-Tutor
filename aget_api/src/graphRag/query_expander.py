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

from data_models.models import Topics, TopicsFactory
from pymongo import MongoClient

class QueryExpander:
    def __init__(self, db : MongoClient):
        self.db = db
    
    def get_expanded_query(self, query : str, min_weight : float) -> str:
        
        alternative_terms = set()
        query = query.strip().lower()

        #This returns all chunks where the conditions are met:
        cursor = self.db.entity_edges_collection.find(
                                                        {
                                                            "$or" : [
                                                                {
                                                                    "relation.source" : query
                                                                },
                                                                {   
                                                                    "relation.target" : query
                                                                }
                                                            ]
                                                        }
                                                    )
        
        #These chunks may contain many relations, some containing the query term, others dont. Cursor will return the entire document
        #So need to select only those relations where the query term is present in either source or target node and the edge weight meets the threshold weight criteria:
        for chunk in cursor:
            for rel in chunk["relation"]:

                if rel["weight"] < min_weight:
                    continue

                if rel["source"] == query:
                    alternative_terms.add(rel["target"])
                
                elif rel["target"] == query:
                    alternative_terms.add(rel["source"])

        print(alternative_terms)
        expanded_query = " ".join([s for s in alternative_terms])

        return expanded_query
    

    
    

