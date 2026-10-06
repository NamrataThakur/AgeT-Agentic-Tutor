#This file contains the retriever creation code:
from dotenv import load_dotenv
load_dotenv()
import warnings

warnings.filterwarnings("ignore")

from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever
from pymongo import MongoClient
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from embeddings.embedders import EmbeddingsCreator

class Retriever:
    def __init__(self, db : MongoClient, embed_model_type = "openai"):
        self.db = db
        self.embedder = EmbeddingsCreator(embed_model_type=embed_model_type)


    def get_vectorstore(self) -> MongoDBAtlasVectorSearch:
        """Creates and returns a hybrid search retriever with the specified embedding model.

        Returns:
            MongoDBAtlasVectorSearch: A configured vector store using vector capabilities.
        """

        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.db.chunks_collection,
            embedding=self.embedder.embed_model,

            #Vector Index Name
            index_name="vector_index",

            #Column in the collection that holds 'document.page_content' values. This is not same as the text_index values.
            text_key=['text'], 

            #Column in the collection that holds the raw embeddings.
            embedding_key="embeddings"
        )


    def get_hybrid_retriever(self, k : int  = 20) -> MongoDBAtlasHybridSearchRetriever:
        """Creates and returns a hybrid search retriever with the specified embedding model.
        This is Langchain compatible.

        Args:
            k (int, optional): Number of documents to retrieve. Defaults to 5.

        Returns:
            MongoDBAtlasHybridSearchRetriever: A configured hybrid search retriever using both
            vector and text search capabilities.
        """
        
        retriever = MongoDBAtlasHybridSearchRetriever(
                    vectorstore=self.vector_store,
                    search_index_name = "text_index",
                    top_k=k,

                    #Penalty applied to vector search results in RRF : score = 1 / (rank + penalty)
                    vector_penalty=50.0,

                    #Penalty applied to text search results in RRF : score = 1 / (rank + penalty)
                    fulltext_penalty=60.0

                    )

        return retriever






