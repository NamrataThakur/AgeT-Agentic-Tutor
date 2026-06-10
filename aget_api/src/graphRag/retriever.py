#This file contains the retriever creation code:
from dotenv import load_dotenv
load_dotenv()
import warnings

warnings.filterwarnings("ignore")

from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers import MongoDBAtlasHybridSearchRetriever

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.mongo import MongoDb
from embeddings.embedders import EmbeddingsCreator

class Retriever:
    def __init__(self, embed_model_type = "openai"):
        self.db = MongoDb()
        self.embedder = EmbeddingsCreator(embed_model_type=embed_model_type)


    def get_retriever(self, k : int  = 5) -> MongoDBAtlasHybridSearchRetriever:
        """Creates and returns a hybrid search retriever with the specified embedding model.

        Args:
            k (int, optional): Number of documents to retrieve. Defaults to 5.

        Returns:
            MongoDBAtlasHybridSearchRetriever: A configured hybrid search retriever using both
            vector and text search capabilities.
        """
        
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.db.chunks_collection,
            embedding=self.embedder,

            #Vector Index Name
            index_name="vector_index",

            #Column in the collection that holds 'document.page_content' values. This is not same as the text_index values.
            text_key=['text'], 

            #Column in the collection that holds the raw embeddings.
            embedding_key="embeddings"
        )


        retriever = MongoDBAtlasHybridSearchRetriever(
                    vectorstore=self.vector_store,
                    search_index_name = "text_index",
                    top_k=k,

                    #Penalty applied to vector search results in RRF : score = 1 / (rank + penalty)
                    vector_penalty=50,

                    #Penalty applied to text search results in RRF : score = 1 / (rank + penalty)
                    fulltext_penalty=50
        )

        return retriever






