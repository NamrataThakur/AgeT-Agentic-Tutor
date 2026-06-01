from langchain_community.embeddings import OllamaEmbeddings, OpenAIEmbeddings
from typing import List, Dict, Literal
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

class EmbeddingsCreator:
    def __init__(self, embed_model_type = Literal['openai'] | str):
        self.model_type = embed_model_type

        #Read the model name from config file:
        if self.model_type == "openai":
            self.embed_model = OpenAIEmbeddings(model="text-embedding-3-large")
        
        elif self.model_type == "ollama":
            self.embed_model = OllamaEmbeddings(model="nomic-embed-text")

        else:
            self.embed_model = SentenceTransformer('all-mpnet-base-v2')

    
    def embedding_creation_pipeline(self, chunks : List[Document]) -> List[List[float]]:

        sentences = [ch.page_content for ch in chunks]
        if self.model_type == "ST":
            embeddings = self.embed_model.encode(sentences)
        else:
            embeddings = self.embed_model.embed_documents(texts=sentences)

        assert len(chunks) == len(embeddings)
        return embeddings

