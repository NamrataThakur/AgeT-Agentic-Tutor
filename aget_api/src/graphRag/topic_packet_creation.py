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

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

class TopicPacketCreation:
    def __init__(self, db: MongoClient, top_neighbours : int = 10, min_score_2hop : float = 0.2,
                 max_strong_2hop : int = 5, max_weak_2hop : int = 3, min_score_3hop : float = 0.08,
                 max_strong_3hop : int = 3, max_weak_3hop : int = 2):
        
        self.db = db
        self.top_neighbours = top_neighbours
        self.min_score_2hop = min_score_2hop
        self.max_strong_2hop = max_strong_2hop
        self.max_weak_2hop = max_weak_2hop

        self.min_score_3hop = min_score_3hop
        self.max_strong_3hop = max_strong_3hop
        self.max_weak_3hop = max_weak_3hop


    def get_unique_entities(self, chunks : List[Dict], equation : bool = False) -> tuple[Set[str] | None, 
                                                                                         Set[str] | None, 
                                                                                         None | Set[tuple]]:

        unq_entities = set()
        unq_chunk_text = set()
        unq_equation_entities = set()

        #Chunks can come from only Chunk Expansion, only Vector Search or only BM25 search:
        for chunk in chunks:

            #Only From Chunk Expansion:
            if chunk.get("expansion_rank", 0) != 0:

                if equation:
                    unq_equation_entities.update([(chunk["chunk_id"], chunk["text"], ent["normalized_text"]) 
                                                  for ent in chunk["entities"] 
                                                    if ent["label"] == "equation"])
                else:
                    unq_chunk_text.add(chunk["text"])
                    unq_entities.update([ent["normalized_text"] for ent in chunk["entities"]])

            #From RRF Retrieval:
            else:
                #Either From Vector Search:
                if chunk["vector_rank"] is not None:

                    if equation:
                        unq_equation_entities.update([(chunk["chunk_id"], chunk["docs"].page_content, ent["normalized_text"]) 
                                                      for ent in chunk["docs"].metadata["entities"] 
                                                        if ent["label"] == "equation"])
                        
                    else:
                        unq_chunk_text.add(chunk["docs"].page_content)
                        unq_entities.update([ent["normalized_text"] for ent in chunk["docs"].metadata["entities"]])
                    
                    
                #Only from BM25 Search:
                else:

                    if equation:
                        unq_equation_entities.update([(chunk["chunk_id"], chunk["docs"]["text"], ent["normalized_text"]) 
                                                      for ent in chunk["docs"]["entities"] 
                                                       if ent["label"] == "equation"])
                    else:
                        unq_chunk_text.add(chunk["docs"]["text"])
                        unq_entities.update([ent["normalized_text"] for ent in chunk["docs"]["entities"]])

                   
        return (unq_entities, unq_chunk_text, unq_equation_entities)
    
    
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
                    "explanation" : edge_info.get("explanation", ""),
                    "edge_type" : edge_info.get("edge_type", "")

                })

            #Get top neighbours for each of the entities:
            neighbours = sorted(neighbours, key=lambda x: x["weight"], reverse=True)[:self.top_neighbours]

            #Dont add entities if it has no neighbours:
            if len(neighbours) == 0:
                continue

            entity_neighbours[entity] = neighbours

        return entity_neighbours
    

#----------------- EQUATION PATHS START ----------------------------------------------------------------------
    def get_equation_paths(self, chunks : List[Dict], equation : bool = True):

        equation_paths = dict()

        _, _, unq_eq_ent = self.get_unique_entities(chunks=chunks, equation=equation)

        #Forming the "mentions" relations:
        equation_paths["retrieved_equations"] = self.get_retrieved_equation_paths(retrieved_info=unq_eq_ent)

        chunk_ids = list(set([id for id, text, equations in unq_eq_ent]))
        unq_eq_entities = set([equation for id, text, equation in unq_eq_ent])

        #Creating the E-R graph to look for 'co-occur' relations between the equation entities:
        e_r_eq_graph = self.create_entity_relation_graph(unq_entities=unq_eq_entities, chunk_ids=chunk_ids)

        neighbours = self.get_neighbours(e_r_graph=e_r_eq_graph, unq_entities=unq_eq_entities)
        

        # co_occur_unq_eq_entities = {'p_{k}=1', 'y_{k}=1', 
        #                     'y_{k}=0', 
        #                     'p_{k}=0', 'p_{k}=0', 'y=beta_{0}+beta_{1}x'}

        # co_occur_chunk_ids = ["c66a2717-1d1c-459b-9e24-c33bc94b491b"]

        if len(neighbours) == 0:
            print("No co-occurs relation for any of the equation node selected..!")
            equation_paths["related_paths"] = []
        else:
            equation_paths["related_paths"] = self.get_related_equation_paths(retrieved_info=neighbours)
     
        file_path = settings.INTERMITTENT_DATA / "equation_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(equation_paths, f, indent=4)

        return equation_paths
    

    def get_retrieved_equation_paths(self, retrieved_info : Set[tuple]) :

        #Update this function once the graphs contain the "mentions" relations:

        paths = []
        for id, text, eq in retrieved_info:
            obj = {
                "source" : text,
                "relation" : "mentions",
                "target" : eq,
                "weight" : 0.5,
            }
            paths.append(obj)

        return paths
    

    def get_related_equation_paths(self, retrieved_info : Dict):

        #Logic to select the 'co-occurs' relations between equation entities:
        all_paths = []
        seen_pairs = set()

        for equation, neighbours in retrieved_info.items():
            
            for neigh in neighbours:
                target = neigh["neighbour"]

                if equation == target:
                    continue

                key = tuple(sorted((equation, target)))
                if key in seen_pairs:
                    continue

                seen_pairs.add(key)

                obj = {
                    "source" : equation,
                    "relation" : neigh["relation"],
                    "target" : target,
                    "weight" : neigh["weight"],
                    "explanation" : neigh["explanation"],
                    "edge_type" : neigh["edge_type"]
                }
                
                all_paths.append(obj)

        return all_paths

#----------------- EQUATION PATHS ENDS ----------------------------------------------------------------------

    
#----------------- CONCEPT PATHS START ----------------------------------------------------------------------
    
    def get_2_hop_paths(self, e_r_graph : nx.Graph, neigh_entities : Dict, equation : bool = False) -> Dict:
        
        all_paths = dict()

        for ent, neighbour in neigh_entities.items():
            
            #List to hold all paths for the original entity:
            list_paths = []

            #First Level:
            for neigh in neighbour:
                first_lev_path = {
                    "source" : ent,
                    "relation" : neigh["relation"],
                    "target" : neigh["neighbour"],
                    "weight" : neigh["weight"],
                    "explanation" : neigh["explanation"],
                    "edge_type" : neigh.get("edge_type", "")
                }
            
                #Second Level:
                for sec_neigh in e_r_graph.neighbors(neigh["neighbour"]):
                    sec_neigh_list = []
                    sec_neigh_list.append(first_lev_path)

                    edge_data = e_r_graph.get_edge_data(u=neigh["neighbour"],
                                                        v=sec_neigh)
                    
                    path = {
                        "source" : neigh["neighbour"],
                        "relation" : edge_data["relation"],
                        "target" : sec_neigh,
                        "weight" : edge_data.get("weight",1.0),
                        "explanation" : edge_data.get("explanation", ""),
                        "edge_type" : edge_data.get("edge_type", "")
                    }
                    sec_neigh_list.append(path)
                    list_paths.append(sec_neigh_list)

            all_paths[ent] = list_paths


        #file_name = "all_2_hop_paths_equation.json" if equation else "all_2_hop_paths.json"
        file_path = settings.INTERMITTENT_DATA / "all_2_hop_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_paths, f, indent=4)

        return all_paths
    

    #Pruning logic:
    def prune_2_hop_paths(self, paths : Dict, min_score_2hop : float, equation : bool = False) -> Dict:

        #Pruning the paths based on 3 criterias: 
        #                                         a) cyclic paths [A -> B -> A], 
        #                                         b) consecutive 'co-occurs' relations, 
        #                                         c) path_score < min_score_2hop


        pruned_paths = dict()

        for entitiy, overall_paths in paths.items():
            
            prune_ent_path = []
            for path in overall_paths:

                #Prune consecutive 'co-occurs' relations:
                co_occur_count = sum(rel["relation"] == "co_occurs" for rel in path)
                if co_occur_count == 2:
                    continue
                
                #Prune cyclic paths [A -> B -> A]
                if path[0]["source"] == path[1]["target"]:
                    continue
                
                #Prune path_score < min_score
                if path[0]["weight"] * path[1]["weight"] < min_score_2hop:
                    continue
                
                #Assign path quality to selectively filter later on:
                semantic_count = sum(rel["relation"] != "co_occurs" for rel in path)
                quality = "strong" if semantic_count == 2 else "weak"

                #Do not mutate the raw path with path.append(...)
                prune_ent_path.append({
                        "path": [path[0], path[1]],
                        "path_score" : round(path[0]["weight"] * path[1]["weight"], 6),
                        "path_quality": quality
                    }
                )

            #Sort all the pruned paths:
            sorted_pruned_paths = sorted(prune_ent_path, key=lambda x: x["path_score"], reverse=True)

            if len(sorted_pruned_paths) > 0:
                pruned_paths[entitiy] = sorted_pruned_paths      

        #file_name = "pruned_2_hop_paths_equation.json" if equation else "pruned_2_hop_paths.json"
        file_path = settings.INTERMITTENT_DATA / "pruned_2_hop_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(pruned_paths, f, indent=4)

        return pruned_paths
                    
    
    #Select the best pruned paths:
    def select_2hop_paths(self, pruned_paths, max_strong : int, max_weak : int, equation : bool = False) -> Dict:

        filtered_paths = {}

        for entity, overall_paths in pruned_paths.items():
            strong_paths = []
            weak_paths = []

            for path in overall_paths:

                if path["path_quality"] == "strong":
                    strong_paths.append(path)
                    
                else:
                    weak_paths.append(path)

            if strong_paths:
                strong_paths = sorted(strong_paths, key = lambda x: x["path_score"], reverse=True)[:max_strong]
                
            if weak_paths:
                weak_paths = sorted(weak_paths, key = lambda x: x["path_score"], reverse=True)[:max_weak]
                
            total_paths = strong_paths + weak_paths

            filtered_paths[entity] = total_paths

        #file_name = "filtered_2_hop_paths_equation.json" if equation else "filtered_2_hop_paths.json"
        file_path = settings.INTERMITTENT_DATA / "filtered_2_hop_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(filtered_paths, f, indent=4)

        return filtered_paths


    def get_3_hop_paths(self, e_r_graph : nx.Graph, neigh_entities : Dict) -> Dict:

        all_paths = dict()

        for ent, neighbour in neigh_entities.items():
            
            #List to hold all paths for the original entity:
            list_paths = []

            #First Level:
            for neigh in neighbour:
                first_lev_path = {
                                    "source" : ent,
                                    "relation" : neigh["relation"],
                                    "target" : neigh["neighbour"],
                                    "weight" : neigh["weight"],
                                    "explanation" : neigh["explanation"],
                                    "edge_type" : neigh.get("edge_type", "")
                                }
            
                #Second Level:
                for sec_neigh in e_r_graph.neighbors(neigh["neighbour"]):


                    edge_data = e_r_graph.get_edge_data(u=neigh["neighbour"],
                                                        v=sec_neigh)
                    
                    sec_lev_path = {
                                        "source" : neigh["neighbour"],
                                        "relation" : edge_data["relation"],
                                        "target" : sec_neigh,
                                        "weight" : edge_data.get("weight",1.0),
                                        "explanation" : edge_data.get("explanation", ""),
                                        "edge_type" : edge_data.get("edge_type", "")
                                    }

                    #Third Level:
                    for third_neigh in e_r_graph.neighbors(sec_neigh):

                        third_neigh_list = []
                        third_neigh_list.append(first_lev_path)
                        third_neigh_list.append(sec_lev_path)

                        edge_data = e_r_graph.get_edge_data(u=sec_neigh,
                                                            v=third_neigh)
                        
                        path = {
                                    "source" : sec_neigh,
                                    "relation" : edge_data["relation"],
                                    "target" : third_neigh,
                                    "weight" : edge_data.get("weight",1.0),
                                    "explanation" : edge_data.get("explanation", ""),
                                    "edge_type" : edge_data.get("edge_type", "")
                                }

                        third_neigh_list.append(path)
                        list_paths.append(third_neigh_list)
               

            all_paths[ent] = list_paths

        file_path = settings.INTERMITTENT_DATA / "all_3_hop_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(all_paths, f, indent=4)

        return all_paths
    

    def prune_3_hop_paths(self, paths: Dict, min_score_3hop: float) -> Dict:

        pruned_paths = {}

        for entity, overall_paths in paths.items():

            pruned_entity_paths = []

            for path in overall_paths:

                # Must be exactly: A -> B -> C -> D
                if len(path) != 3:
                    continue

                edge_1, edge_2, edge_3 = path

                # ---------------------------------------------------------
                # 1. Validate connected path:
                # A -> B -> C -> D
                # ---------------------------------------------------------
                if (
                    edge_1["target"] != edge_2["source"]
                    or edge_2["target"] != edge_3["source"]
                ):
                    continue

                node_a = edge_1["source"]
                node_b = edge_1["target"]
                node_c = edge_2["target"]
                node_d = edge_3["target"]

                # ---------------------------------------------------------
                # 2. Prune all repeated-node / cyclic paths:
                # A -> B -> C -> A
                # A -> B -> B -> C
                # A -> B -> C -> B
                # Also catches any other repeated-node case.
                # ---------------------------------------------------------
                nodes = [node_a, node_b, node_c, node_d]

                if len(nodes) != len(set(nodes)):
                    continue

                rel_1 = edge_1["relation"]
                rel_2 = edge_2["relation"]
                rel_3 = edge_3["relation"]

                # ---------------------------------------------------------
                # 3. Prune consecutive co_occurs:
                # co_occurs -> co_occurs -> X
                # X -> co_occurs -> co_occurs
                #
                # Does NOT remove:
                # co_occurs -> semantic_relation -> co_occurs
                # ---------------------------------------------------------
                if (
                    (rel_1 == "co_occurs" and rel_2 == "co_occurs")
                    or (rel_2 == "co_occurs" and rel_3 == "co_occurs")
                ):
                    continue

                # ---------------------------------------------------------
                # 4. Prune low-score paths
                # ---------------------------------------------------------
                path_score = (
                    edge_1["weight"]
                    * edge_2["weight"]
                    * edge_3["weight"]
                )

                if path_score < min_score_3hop:
                    continue

                # ---------------------------------------------------------
                # 5. Quality label
                # Strong = all 3 edges are semantic relations
                # Weak   = at least 1 co_occurs relation
                # ---------------------------------------------------------
                semantic_count = sum(relation != "co_occurs" for relation in (rel_1, rel_2, rel_3))

                quality = "strong" if semantic_count == 3 else "weak"

                # Do not mutate the raw path with path.append(...)
                # It can corrupt future processing if this method is rerun.
                pruned_entity_paths.append(
                    {
                        "path": [edge_1, edge_2, edge_3],
                        "path_score": round(path_score, 6),
                        "path_quality": quality
                    }
                )

            if pruned_entity_paths:
                pruned_entity_paths.sort(key=lambda x: x["path_score"],reverse=True)

                pruned_paths[entity] = pruned_entity_paths

            file_path = settings.INTERMITTENT_DATA / "pruned_3_hop_paths.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(pruned_paths, f, indent=4)

        return pruned_paths
    

    def select_3hop_paths(self,pruned_paths: Dict, max_strong: int, max_weak: int) -> Dict:

        filtered_paths = {}

        for entity, overall_paths in pruned_paths.items():

            strong_paths = [
                path for path in overall_paths
                if path["path_quality"] == "strong"
            ]

            weak_paths = [
                path for path in overall_paths
                if path["path_quality"] == "weak"
            ]

            # `pruned_paths` is already score-sorted, but sorting here
            # makes this method safely independent.
            strong_paths = sorted(strong_paths, key=lambda x: x["path_score"], reverse=True)[:max_strong]

            weak_paths = sorted(weak_paths, key=lambda x: x["path_score"], reverse=True)[:max_weak]

            total_paths = strong_paths + weak_paths

            if total_paths:
                filtered_paths[entity] = total_paths

        file_path = settings.INTERMITTENT_DATA / "filtered_3_hop_paths.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(filtered_paths, f, indent=4)

        return filtered_paths

#----------------- CONCEPT PATHS ENDS ----------------------------------------------------------------------
    
    def topic_packet_creation_pipeline(self, chunks : List[Dict]) -> Dict:

        print('--------------- TOPIC PACKET CREATION STARTED -------------------------')

        topic_packet = dict()

        #Select all unique entities across all chunks:
        unq_enitites, chunk_text, _ = self.get_unique_entities(chunks=chunks, equation=False)
        print(f"Unique Entities Extracted : {len(unq_enitites)}")

        topic_packet["core_concepts"] = unq_enitites
        topic_packet["supporting_chunks"] = chunk_text

        chunk_ids = [chk["chunk_id"] for chk in chunks]

        #Create entity-relation graph using all entities across all chunks:
        entity_relation_graph = self.create_entity_relation_graph(unq_entities=unq_enitites, chunk_ids=chunk_ids)
        print(f"Entity-Relation Graph created for the {len(chunks)} chunks..!")

        #Get top neighbours for each of the entities:
        neighbours = self.get_neighbours(e_r_graph=entity_relation_graph, unq_entities=unq_enitites)    
        print("Neighbour Extraction Completed..!")    

        #Get 2-hop paths for each of entities having neighbours:
        ent_2_hop_paths = self.get_2_hop_paths(e_r_graph= entity_relation_graph, neigh_entities= neighbours)

        #Prune the 2-hop paths:
        pruned_2_hop_paths = self.prune_2_hop_paths(paths = ent_2_hop_paths, min_score_2hop = self.min_score_2hop)
        top_2_hop_paths = self.select_2hop_paths(pruned_paths=pruned_2_hop_paths, 
                                                  max_strong = self.max_strong_2hop,
                                                  max_weak = self.max_weak_2hop)
        print("BEST 2-hop concept paths selection completed..!")

        #Get 3-hop paths for each of entities having neighbours:
        ent_3_hop_paths = self.get_3_hop_paths(e_r_graph=entity_relation_graph, neigh_entities=neighbours)
        
        #Prune the 3-hop paths:
        pruned_3_hop_paths = self.prune_3_hop_paths(paths = ent_3_hop_paths, min_score_3hop = self.min_score_3hop)
        top_3_hop_paths = self.select_3hop_paths(pruned_paths=pruned_3_hop_paths, 
                                                  max_strong = self.max_strong_3hop,
                                                  max_weak = self.max_weak_3hop)
        print("BEST 3-hop concept paths selection completed..!")

        equation_paths = self.get_equation_paths(chunks=chunks, equation=True)
        print("Equation paths selection completed..!")

        topic_packet["concept_paths"] = {"2_hop" : top_2_hop_paths, "3_hop" : top_3_hop_paths}
        topic_packet["retrieved_equations"] = equation_paths["retrieved_equations"]
        topic_packet["related_equations"] = equation_paths["related_paths"] 

        print('--------------- TOPIC PACKET CREATION COMPLETED -------------------------')
        return topic_packet