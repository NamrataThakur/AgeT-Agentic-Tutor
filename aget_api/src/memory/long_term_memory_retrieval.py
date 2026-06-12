#

from dotenv import load_dotenv
load_dotenv()

from typing import List
from langchain_core.documents import Document

import warnings

warnings.filterwarnings("ignore")

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graphRag.retriever import Retriever


class LongTermMemoryRetrieval:
    def __init__(self, model_type = 'openai', k : int= 20, similarity_threshold : float = 0.3) -> Retriever:
        self.ret = Retriever(embed_model_type=model_type)
        self.ret.get_vectorstore()

        self.retriever = self.ret.get_hybrid_retriever(k=k)

        self.similarity_threshold = similarity_threshold


    def get_hybrid_retrieval(self, query : str, filter_value : str) -> List[Document]:
        
        documents = self.retriever.invoke(input=query,
                                          filter={
                                              "document_id" : filter_value
                                          })

        return documents
    

    def get_vector_retrieval(self, query : str,  filter_value : str) -> List[Document]:

        vector_retriever = self.ret.vector_store.as_retriever(
                                                            search_type="similarity_score_threshold",
                                                            search_kwargs={"score_threshold": self.similarity_threshold,
                                                                           "pre_filter" : {
                                                                               "document_id" : filter_value
                                                                            }
                                                                           },

                                                        )
        
        documents = vector_retriever.invoke(input=query)

        return documents
