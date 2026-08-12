from langchain_community.embeddings import OllamaEmbeddings, OpenAIEmbeddings
from typing import List, Dict, Literal
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from config.settings import settings

class EmbeddingsCreator:
    def __init__(self, embed_model_type = Literal['openai'] | str):
        self.model_type = embed_model_type
        print(f"Embedding Model : {self.model_type}")
        
        #Read the model name from config file:
        if self.model_type == "openai":
            #Check how to give dimension value. Need dim=1024
            self.embed_model = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL_ID) 
            
        elif self.model_type == "ollama":
            self.embed_model = OllamaEmbeddings(model=settings.OLLAMA_EMBEDDING_MODEL_ID)

        else:
            self.embed_model = SentenceTransformer(settings.ST_EMBEDDING_MODEL_ID)

    
    def embedding_creation_pipeline(self, chunks : List[Document]) -> List[List[float]]:

        sentences = [ch.page_content for ch in chunks]
        if self.model_type == "ST":
            embeddings = self.embed_model.encode(sentences)
        else:
            embeddings = self.embed_model.embed_documents(texts=sentences)

        assert len(chunks) == len(embeddings)
        print(f"Embeddings created for {len(chunks)} chunks..!")
        print("----------------------------------------------------------------------------")
        return embeddings
    
    
    def get_query_embeddings(self, query : str | List[str]) -> List[float] | List[List[float]]:

        if type(query) == str:
            if self.model_type == "ST":
                embeddings = self.embed_model.embed_query(query)

            else:
                embeddings = self.embed_model.embed_query(text=query)

        else:
            if self.model_type == "ST":
                embeddings = self.embed_model.embed_documents(query)

            else:
                embeddings = self.embed_model.embed_documents(texts=query)

        return embeddings

