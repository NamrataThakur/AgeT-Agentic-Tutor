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
from graphRag.retriever import Retriever
from graphRag.re_ranker import ReRanker
from knowledge_base.knowledge_base_langchain_retrieval import LangchainRetrieval
from knowledge_base.knowledge_base_custom_retrieval import CustomRetrieval
from graphRag.query_expander import QueryExpander
from graphRag.chunk_expander import ChunkExpander
from graphRag.topic_packet_creation import TopicPacketCreation
from db.mongo import MongoDb

#PIPELINE DESCRIPTION ::::: 
# =============================== GRAPH RAG BEGINS ==================================

# ================================================== RAG BEGINS ================================
# 1. Input Query --> TopicDetection (Done)
# 2. TopicDetection --> List of Topics (Done)
# 3. Get the topic_id of each of those topics --> Pre-filtering using topic_id as metadata (Done)
# 4. Query Expansion [log reg --> logistic regression] --> Expanded Query to go into BM25 and Re-Ranker System (Done)
# 5. Hybrid retrieval using RRF --> Top 'K' chunks (Done)
# 6. Re-ranking of results using Re-ranker to get top 'M' chunks (Done)
# =================================================== RAG ENDS ==================================

# =============================== GRAPH EXPANSION BEGINS ==================================
# 1. Select top 10 chunks from re-ranker output (Done)
# 2. Perform Chunk Expansion using these 10 chunks as seed (Done)
# 2a. Take all the neighbours of each seed chunks (Done)
# 2b. For each seed chunk, score each neighbour using seed chunk's reranker score and neighbour's edge weight (Done)
# 2c. Select top 15 unique neighbour chunks across all seed chunks --> Deduplication across all seed chunks (Done)
# 3. Total chunks : 10 (seed) + 15 (top neighbours) = 25 --> Chunk Expansion complete (Done)
#--------------------------------------------------------------------------------------------------------------
# 4. Topic Packets Creation Start: Across all 25 chunks:
# 4a. Select all unique entities across 25 chunks (Done)
# 4b. Create entity-relation graph using all entities across 25 chunks (Done)
# 4c. Get 5 neighbours for each of the entities (x) using the E-R graph --> Total entity : 5 * x = 5x (Done)
# 4d. Get unique 2-hop paths for each of these (x) entities --> Upto 5 strong and upto 3 weak paths for each original entity --> Total 2-hop paths : 25 * x = 25x == 131 (Done)
# 4e. Get unique 3-hop paths for each of these (x) entities --> Upto 3 strong and upto 2 weak paths for each original entity --> Total 3-hop paths : 25 * x = 25x == 88(Done)
# 4f. Total concept paths: 25x (2-hop) + 25x (3-hop) = 50x == 219 --> Across all entities having 5 neighbours (Done)
# 4g. Across 25 chunks: Get the chunks having 'equations' as entity types --> Retrieved chunks have this info (Done)
# 4h. Get the 'mention's relations for each of these 'equation' entities --> { chunk_id, chunk_text, relation_type, equation} --> Use 'entity-relation' collection (Done)
#            --> This relation_type is currently not existing in the mongodb data. 
#                Code is ready but new code has not been run as of now. 
#                So prep the code for this but dont run this for now. (Done)
# 4i. Get the 'co-occurs' relations for each of these 'equation' entities --> { chunk_id, text, source_eq, relation_type, target_eq} --> Use 'entity-relation' collection (Done)
# 4j. Add Chunk text from all 25 chunks as 'supporting chunk' key in topic packet (Done)
# 4h. Topic Packets ={ entities, supporting chunk, concept paths : {'2-hop' : {[]}, '3-hop' : {[]} }, 
#                      retrieved_equations : [{}],  related_equations : [{}]} (Done)
# =============================== GRAPH EXPANSION ENDS ==================================

# =============================== GRAPH RAG ENDS ==================================

class GraphRAGPipeline:
    def __init__(self, model_type : str = "openai", top_k : int = 30, rerank_k : int = 20, 
                                                    chunk_expand_k : int = 10, #Top 'k' chunks selected out of re-ranked results as seed
                                                    chunk_expand_n : int = 15, #Top 'n' chunks added as a part of chunk expansion 
                                                    similarity_threshold : float = 0.7,
                                                    edge_min_weight : float = 0.3,
                                                    top_entity_neighbours : int = 10,
                                                    min_score_2hop : float = 0.2, 
                                                    max_strong_2hop : int = 5, max_weak_2hop : int = 3,
                                                    min_score_3hop : float = 0.2,
                                                    max_strong_3hop : int = 3, max_weak_3hop : int = 2):
        
        self.topic_detector = TopicDetection()

        #Langchain based retrieval:
        #self.retriever = LangchainRetrieval(model_type=model_type, k=top_k, similarity_threshold= similarity_threshold )
        self.db = MongoDb()

        #Custom Retrieval:
        self.custom_retriever = CustomRetrieval(model_type=model_type, k=top_k, 
                                                              similarity_threshold= similarity_threshold,
                                                              db=self.db)
        self.reranker = ReRanker(k=rerank_k)
        self.query_expander = QueryExpander(db = self.db)
        self.edge_min_weight = edge_min_weight
        self.chunk_expander = ChunkExpander(db=self.db, top_k=chunk_expand_k, expanded_chunk_length=chunk_expand_n)
        self.topic_packet = TopicPacketCreation(db=self.db, top_neighbours=top_entity_neighbours,
                                                min_score_2hop=min_score_2hop, 
                                                max_strong_2hop=max_strong_2hop,
                                                max_weak_2hop=max_weak_2hop, 
                                                min_score_3hop=min_score_3hop, 
                                                max_strong_3hop=max_strong_3hop,
                                                max_weak_3hop=max_weak_3hop)
        

    def pipeline(self, query : str, vector_weight : float, bm25_weight : float):

        print(f"Original Query : {query}")
        
        #Step 0. Topic Extraction from the query
        extracted_topics, message = self.topic_detector.get_topic(query=query)

        topic_list = []
        topic_packets = dict()

        if message == "Topic NOT Found in Knowledge Base..!":

            return extracted_topics, message
        
        #TO DO: IF more than one topic is detected, clarify with user which one to select --> TO be done during Agent implementation
        print(message)

        #For now, use all topics detected:
        for topic in extracted_topics:
            print(f"Topic : {topic.id}")
            normalized_query = topic.name
            print(f"Normalized Query : {normalized_query}")

            #Step 1. Query Expansion for BM25 Search and Re-Ranker:
            print("-------------------- QUERY EXPANSION STARTED --------------------")
            expanded_query = self.query_expander.get_expanded_query(query=normalized_query, 
                                                                    min_weight=self.edge_min_weight,
                                                                    )
            print(f"Expanded Query : {expanded_query}")
            print("-------------------- QUERY EXPANSION COMPLETED --------------------")


            #Step 2. Hybrid retrieval using RRF:
            custom_retrieved_docs = self.custom_retriever.custom_retrieval_pipeline(query=normalized_query, 
                                                                                    expanded_query=expanded_query,
                                                                                    filter_value=str(topic.id),
                                                                                    vector_weight=vector_weight, 
                                                                                    bm25_weight=bm25_weight)
            topic_list.append(custom_retrieved_docs)

            #Step 3. Re-ranking of results using Re-ranker:
            reranked_docs = self.reranker.get_reranked_chunks(query=query, rrf_results=custom_retrieved_docs)

            #Step 4. Chunk Expansion:
            expanded_docs = self.chunk_expander.chunk_expansion_pipeline(reranked_chunks=reranked_docs)
            
            #Step 5: Topic Packets Creation:
            topic_packets = self.topic_packet.topic_packet_creation_pipeline(chunks=expanded_docs)
            topic_packets["topic_id"] = topic.id

        return topic_packets
    


if __name__ == "__main__":
    pipeline = GraphRAGPipeline()
    docs = pipeline.pipeline(query="ask me on logistic regression", vector_weight=0.5, bm25_weight=0.5)
    print('-------------------------------------')
    print((docs.keys()))
    #print(docs)
    print('-------------------------------------')
    # print((docs[1].keys()))
    # print(len(list((docs[1].keys()))))
    #print('-------------------------------------')
    print(len(docs))


        
        



