from typing import List, Dict
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import uuid
from enum import Enum

CHUNK_EDGE_THRESHOLD = 0.72

class GraphBuilder:
    def __init__(self):
        self.chunk_graph = nx.MultiDiGraph()
        self.entity_graph = nx.MultiDiGraph()


    def create_semantic_chunk_collection(self, chunk_list : List[Dict]) -> List[Dict]:

        print("Building chunk graph...")
        semantic_chunk_list = []

        for i in tqdm(range(len(chunk_list))):
            c1 = chunk_list[i]
            c1_entities = c1['entities']
            c1_norm_entities = set([e['normalized_text'] for e in c1_entities])

            for j in range(i+1, len(chunk_list)):
                c2 = chunk_list[j]
                c2_entities = c2['entities']
                c2_norm_entities = set([e['normalized_text'] for e in c2_entities])

                cos_sim = cosine_similarity(X=[c1['embeddings']], Y=[c2['embeddings']])[0][0]
                shared_entities = list(c1_norm_entities.intersection(c2_norm_entities))

                if cos_sim >= CHUNK_EDGE_THRESHOLD or len(shared_entities) > 0:
                    obj = {
                        "source_chunk" : c1['chunk_id'],
                        "target_chunk" : c2['chunk_id'],
                        "shared_entities" : shared_entities,
                        "similarity" : float(cos_sim)
                    }
                    semantic_chunk_list.append(obj)


        return semantic_chunk_list
    


    def create_semantic_chunk_graph(self, chunk_list : List[Dict]):

        print("Building semantic chunk graph...")

        for sem_chunk in chunk_list:
            edge_key = (
                        f"{sem_chunk['source_chunk']}_"
                        f"{sem_chunk['target_chunk']}_"
                        f"{uuid.uuid4()}"
)
            self.chunk_graph.add_node(sem_chunk['source_chunk'])
            self.chunk_graph.add_node(sem_chunk['target_chunk'])
            self.chunk_graph.add_edge(sem_chunk['source_chunk'], 
                                            sem_chunk['target_chunk'],
                                            shared_entities=len(sem_chunk['shared_entities']),
                                            weight=sem_chunk['similarity'],
                                            key=edge_key)


        nx.write_gexf(self.chunk_graph, "chunk_graph.gexf")
        print("Semantic Chunk Graph Completed..!")
        print("------------------------------------------------------------------------")
    

    def create_entity_graph(self, relation_list : List[Dict], entity_list : List[Dict]):
        print("Building Relation Entity Graph...")

        for chunk in relation_list:
            chunk_id = chunk['chunk_id']
            chunk_relations = chunk['relation']
            chunk_entity = [chunk.get("entities",[]) for chunk in entity_list if chunk.get("chunk_id") == chunk_id][0]
            chunk_norm_entity = [(ch['normalized_text'], ch['label']) for ch in chunk_entity]

            self.entity_graph.add_node(chunk_id, type="chunk")

            for ch_entity, ch_type in chunk_norm_entity:
                self.entity_graph.add_node(ch_entity, type=ch_type)
                self.entity_graph.add_edge(u_for_edge=chunk_id,
                                          v_for_edge=ch_entity,
                                          relation="mentions",
                                          weight=0.5)
                
            
            for rel in chunk_relations:
                edge_key = (
                        f"{rel['source']}_"
                        f"{rel['target']}_"
                        f"{uuid.uuid4()}")
                self.entity_graph.add_node(rel['source'])
                self.entity_graph.add_node(rel['target'])
                self.entity_graph.add_edge(rel['source'], 
                                            rel['target'],
                                            relation=(rel['relation'].value if isinstance(rel['relation'], Enum) 
                                                                            else rel['relation']),
                                            weight=rel['weight'],
                                            type=rel['edge_type'],
                                            key=edge_key)

        nx.write_gexf(self.entity_graph, "entity_graph.gexf")
        print("Relation Entity Graph Completed..!")
        print("------------------------------------------------------------------------")
    