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
import uuid

from graphRag.entity_extractor import EntityExtractor
from graphRag.relation_extractor_llm import RelationExtractor
from ingestion.loader import InformationExtractor
from ingestion.chunker import ChunkCreator
from data_models.models import TopicsExtract, Topics, TopicsFactory
from data_models.chunk import ChunkBatch
from data_models.entity_relation import RelationAllBatch
from data_models.chunk_graph import SemanticChunkBatch
from embeddings.embedders import EmbeddingsCreator
from db.mongo import MongoDb
from graphRag.graph_builder import GraphBuilder

ENTITY_LABELS = ["statistical concept", "statistical unit",
    "mathematical concept",
    "probability concept",
    "optimization concept",
    "machine learning concept", "statistical model",
    "machine learning model", "machine learning variable",
    "algorithm","mathematical function",
    "activation function",
    "loss function",
    "parameter",
    "coefficient",
    "hyperparameter","metric",
    "statistical metric",
    "evaluation metric","probability distribution",
    "optimization algorithm",
    "objective function",
    "mathematical expression","statistical transformation",
    "mathematical transformation"]


class LongTermMemoryCreator:
    def __init__(self, model_type = Literal['openai'] | str):
        self.info_extract = InformationExtractor()
        self.chunker = ChunkCreator(embed_model_type="openai")
        self.entity_extractor = EntityExtractor(labels=ENTITY_LABELS, threshold=0.4)
        self.relation_extractor = RelationExtractor()
        self.embedder = EmbeddingsCreator(embed_model_type="openai")
        self.db = MongoDb()
        self.graph_builder = GraphBuilder()

    def create_memory(self, topics : List[TopicsExtract]):
        
        #Call the InformationExtractor --> List of documents for each topic
        topic_gen = self.info_extract.get_extractor(topics=topics)

        #Call ChunkCreator --> List of semantic chunks
        docs_chunks = self.chunker.get_semantic_chunks(documents=topic_gen[1])
        topic_id = topic_gen[0].id
        print(f"Extraction and Chunking pipeline complete for {topic_id}..!")
        print(f"Total semantic chunks created : {len(docs_chunks)}")
        print("==================================================================================")

        #Get the embeddins for all the chunks:
        doc_embeddings = self.embedder.embedding_creation_pipeline(chunks=docs_chunks)

        print(f"Chunk Wise Entity and Relation Extraction Pipeline Started..!")
        chunk_details = []
        relation_details = []

        #Iterate over the chunks to create the records for 'Chunk' and 'entity_edges' Collection
        for idx, chunk in enumerate(docs_chunks):
        
            try:
                print(f"Chunk ID : {idx}")
                chunk_dict = {}
                relation_dict = {}

                chunk_id = str(uuid.uuid4())
                chunk_emb = doc_embeddings[idx]
                chunk_text = chunk.page_content
                document_id = topic_id
                entities = self.entity_extractor.entity_extraction_pipeline(chunk=chunk)
                relations = self.relation_extractor.relation_extraction_pipeline(entities=entities, 
                                                                                 chunk=chunk, 
                                                                                 chunk_id=chunk_id)

                chunk_dict['chunk_id'] = chunk_id
                chunk_dict['document_id'] = document_id
                chunk_dict['source_id'] = "Wikipedia"
                chunk_dict['embeddings'] = chunk_emb
                chunk_dict['entities'] = entities['entities']
                chunk_dict['text'] = chunk_text
                
                relation_dict['chunk_id'] = chunk_id
                relation_dict['relation'] = relations

                chunk_details.append(chunk_dict)
                relation_details.append(relation_dict)
                
            except Exception as e:
                print(f"Error in Chunk : {idx}. Error: {str(e)}")
                print("Byapssing chunking and continuing..!")
                continue

        # 
        print(f"Chunk Wise Entity and Relation Extraction Pipeline Completed..!")
        print("==================================================================================")

        print("==================================================================================")
        print("Ingestion to MongoDB Started for Chunk and Relation Models..!")
        chunk_model = ChunkBatch.model_validate(obj={"chunk_batch" : chunk_details})
        entity_relation_model = RelationAllBatch.model_validate(obj={"relation_batch" : relation_details})

        #Store the records to the 'Chunk' Collection
        self.db.ingest_chunks(document_list=chunk_model.chunk_batch)

        #Store the records to the 'entity_edges' collection
        self.db.ingest_relation(chunk_relation_list=entity_relation_model.relation_batch)

        print("Ingestion to MongoDB Completed for Chunk and Relation Models..!")
        print("==================================================================================")
        
        print("==================================================================================")
        print("Graph Ingestion Started..!")

        #Create the records for the 'semantic chunk graph' collection
        semantic_chunk_details = self.graph_builder.create_semantic_chunk_collection(chunk_list=chunk_details)
        semantic_chunk_model = SemanticChunkBatch.model_validate(obj={"semantic_chunk" : semantic_chunk_details})
        
        #Store the records to the 'Semantic Chunk Graph' collection
        self.db.ingest_chunk_graph(chunk_graph=semantic_chunk_model.semantic_chunk)

        #Create the indexes:
        self.db.create_indexes()
        self.db.create_vector_indexes()

        #Create and store the networkx graph for semantic_chunk
        self.graph_builder.create_semantic_chunk_graph(chunk_list=semantic_chunk_details)

        #Create and store the networkx graph for chunk_entity_relation
        self.graph_builder.create_entity_graph(relation_list=relation_details, entity_list=chunk_details)
        print("Graph Ingestion Completed..!")
        print("==================================================================================")

        print(f"Pipeline completed for {topic_id}..!")