from dotenv import load_dotenv
load_dotenv()

from typing import List, Dict, Set
from langchain_core.documents import Document
from pymongo import MongoClient
import warnings
from collections import defaultdict
import networkx as nx
warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


class TopicPacketCreation:
    def __init__(self, db: MongoClient, top_neighbours : int = 10):
        self.db = db
        self.top_neighbours = top_neighbours


    def get_unique_entities(self, chunks : List[Dict]) -> tuple[Set[str] , Set[str]]:

        unq_entities = set()
        unq_chunk_text = set()

        #Chunks can come from only Chunk Expansion, only Vector Search or only BM25 search:
        for chunk in chunks:

            #Only From Chunk Expansion:
            if chunk.get("expansion_rank", 0) != 0:
                unq_chunk_text.add(chunk["text"])
                unq_entities.update([ent["normalized_text"] for ent in chunk["entities"]])
            
            #From RRF Retrieval:
            else:
                #Either From Vector Search:
                if chunk["vector_rank"] is not None:
                    unq_chunk_text.add(chunk["docs"].page_content)
                    unq_entities.update([ent["normalized_text"] for ent in chunk["docs"].metadata["entities"]])

                #Only from BM25 Search:
                else:
                    unq_chunk_text.add(chunk["docs"]["text"])
                    unq_entities.update([ent["normalized_text"] for ent in chunk["docs"]["entities"]])


        return (unq_entities, unq_chunk_text)
    
    
    def create_entity_relation_graph(self, unq_entities : Set[str], chunk_ids: List[str]) -> nx.Graph:

        graph = nx.Graph()

        #Add all entities as nodes:
        for ent in unq_entities:
            graph.add_node(ent)

        cursor = self.db.entity_edges_collection.find(
                                                        {
                                                            "chunk_id":{
                                                                "$in" : chunk_ids
                                                            }
                                                            
                                                        }
                                                    )
        
        #All edges with relations between all pairs entities:
        for result in cursor:
            relations = result.get("relation", [])

            for rel in relations:
                if rel["source"] in unq_entities and rel["target"] in unq_entities:

                    graph.add_edge(u_of_edge=rel["source"],
                                   v_of_edge=rel["target"],
                                   relation=rel.get("relation"),
                                   weight=rel.get("weight", 1.0),
                                   explanation=rel.get("explanation", ""),
                                   edge_type=rel.get("edge_type", ""))


        return graph
    
    def get_neighbours(self, e_r_graph : nx.Graph, unq_entities : Set[str]) -> Dict:
        
        entity_neighbours = {}

        for entity in unq_entities:

            if entity not in e_r_graph:
                continue

            neighbours = []
            for neighbour in e_r_graph.neighbors(entity):

                edge_info = e_r_graph.get_edge_data(u=entity, v=neighbour)

                neighbours.append({
                    "neighbour" : neighbour,
                    "relation" : edge_info.get("relation", ""),
                    "weight" : edge_info.get("weight", 1.0),
                    "explanation" : edge_info.get("explanation", "")

                })

            #Get top neighbours for each of the entities:
            neighbours = sorted(neighbours, key=lambda x: x["weight"], reverse=True)[:self.top_neighbours]

            #Dont add entities if it has no neighbours:
            if len(neighbours) == 0:
                continue

            entity_neighbours[entity] = neighbours

        return entity_neighbours
    

    
    def get_2_hop_paths(self):
        return
    
    def get_3_hop_paths(self):

        return
    
    def score_paths(self):
        return
    

    
    def topic_packet_creation_pipeline(self, chunks : List[Dict]) -> List:

        topic_packet = dict()

        #Select all unique entities across all chunks:
        unq_enitites, chunk_text = self.get_unique_entities(chunks=chunks)

        topic_packet["core_concepts"] = unq_enitites
        topic_packet["supporting_chunks"] = chunk_text

        chunk_ids = [chk["chunk_id"] for chk in chunks]

        #Create entity-relation graph using all entities across all chunks:
        entity_relation_graph = self.create_entity_relation_graph(unq_entities=unq_enitites, chunk_ids=chunk_ids)

        #Get top neighbours for each of the entities:
        neighbours = self.get_neighbours(e_r_graph=entity_relation_graph, unq_entities=unq_enitites)
        
        return neighbours