#This file handles the semantic chunking of the data extracted from the Wikipedia:

from typing import Literal
from langchain_community.embeddings import OllamaEmbeddings, OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

from loader import InformationExtractor

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graphRag.entity_extractor import EntityExtractor
from graphRag.relation_extractor_llm import RelationExtractor

from pydantic_models.models import TopicsFactory

import os
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "all-MiniLM-L6-v2"


class ChunkCreator:
    def __init__(self, embed_model_type = Literal['openai'] | str):
        self.model_type = embed_model_type

        #Read the model name from config file:
        if self.model_type == "openai":
            self.embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
        
        elif self.model_type == "ollama":
            self.embed_model = OllamaEmbeddings(model="nomic-embed-text")

        else:
            self.embed_model = SentenceTransformer('all-mpnet-base-v2')

    def get_semantic_chunks(self, documents : list[Document] ) -> list[Document]:

        print("Semantic Chunking Stage Started ...!")

        chunker = SemanticChunker(embeddings=self.embed_model, 
                                breakpoint_threshold_type="percentile", 
                                breakpoint_threshold_amount=0.90,
                                min_chunk_size = 400)

        raw_text = "\n\n".join([doc.page_content for doc in documents])
        chunked_docs = chunker.create_documents(texts=[raw_text])

        print("Semantic Chunking Stage Completed ...!")
        return chunked_docs


if __name__ == "__main__":
    log_reg = TopicsFactory().get_topic("logistic_regression")
    docs = InformationExtractor().extract_docs(
        log_reg,
        [
            "https://en.wikipedia.org/wiki/Logistic_regression"
        ],
    )

    chunker = ChunkCreator(embed_model_type="openai")
    semantic_chunks = chunker.get_semantic_chunks(docs)
    print(f"Total semantic chunks created : {len(semantic_chunks)}")
    print(f"Example Chunk : {semantic_chunks[2].page_content}")

    chunk = semantic_chunks[2]

    # ENTITY_LABELS = ["machine learning model", "statistical model", "algorithm", "optimization method", "equation", 
    #                  "mathematical concept", "statistical test", "distribution", "loss function", "metric", "variable",
    #                  "parameter", "scientific concept", "probability concept"] 

    # ENTITY_LABELS = ["statistical model", "mathematical function", "optimization method", "statistical test", "loss function",
    #                 "variable", "parameter", "algorithm", "metric", "probability distribution", "equation", 
    #                 "mathematical transformation", "statistical metric", "probability concept"]

    ENTITY_LABELS = ["statistical concept", "statistical unit",
    "mathematical concept",
    "probability concept",
    "optimization concept",
    "machine learning concept", "statistical model",
    "machine learning model",
    "algorithm","mathematical function",
    "activation function",
    "loss function","variable",
    "parameter",
    "coefficient",
    "hyperparameter","metric",
    "statistical metric",
    "evaluation metric","probability distribution",
    "random variable","matrix",
    "vector",
    "tensor","optimization algorithm",
    "objective function","equation",
    "mathematical expression","statistical transformation",
    "mathematical transformation"]
    
    entity_obj = EntityExtractor(labels=ENTITY_LABELS, threshold=0.4)
    entities = entity_obj.entity_extraction_pipeline(chunk=chunk)

    print(entities)

    relation_obj = RelationExtractor()
    relations = relation_obj.relation_extraction_pipeline(entities=entities, chunk=chunk)

    print(relations)


