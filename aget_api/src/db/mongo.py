#Connect to MongoDB Instance:
from pymongo import MongoClient, errors
from typing import Type, Generic, TypeVar, List
from pydantic import BaseModel

Models = TypeVar("Models", bound=BaseModel)

from dotenv import load_dotenv
import os
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_APPNAME = os.getenv("MONGO_APPNAME")
MONGO_DBNAME = os.getenv("MONGO_DBNAME")
MONGO_CHUNKS_COL = os.getenv("MONGO_CHUNKS_COL")
MONGO_SEM_CHUNKS_COL = os.getenv("MONGO_SEM_CHUNKS_COL")
MONGO_ENTITY_REL_COL = os.getenv("MONGO_ENTITY_REL_COL")


class MongoDb(Generic[Models]):
    """Class for MongoDB operations, supporting ingestion.

    This class provides methods to interact with MongoDB collections, including document
    ingestion.

    Args:
        model (Type[Models]): The Pydantic model class to use for document serialization.
        collection_name (str, optional): Name of the MongoDB collection to use.
        database_name (str, optional): Name of the MongoDB database to use.
        
    Attributes:
        model (Type[Models]): The Pydantic model class used for document serialization.
        collection_name (str): Name of the MongoDB collection.
        database_name (str): Name of the MongoDB database.
        mongodb_uri (str): MongoDB connection URI.
        client (MongoClient): MongoDB client instance for database connections.
        database (Database): Reference to the target MongoDB database.
        collection (Collection): Reference to the target MongoDB collection.
    """

    def __init__(self):

        #Read the db details from config file:        
        try:
            self.db_client = MongoClient(MONGO_URI, appname=MONGO_APPNAME)
            self.db_client.admin.command("ping")
        except Exception as e:
            print(f"Failed to initialize MongoDBService: {e}")
            raise

        self.db_name = MONGO_DBNAME
        self.db = self.db_client[self.db_name]

        self.chunks_collection= self.db[MONGO_CHUNKS_COL]
        self.chunk_edges_collection = self.db[MONGO_SEM_CHUNKS_COL]
        self.entity_edges_collection = self.db[MONGO_ENTITY_REL_COL]

        print(
            f"Connected to MongoDB instance:\n URI: {MONGO_URI}\n Database: {self.db_name}\n "
        )




    def ingest_chunks(self, document_list : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not document_list or not all(isinstance(doc, BaseModel) for doc in document_list):
                raise ValueError("All chunks needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in document_list]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : chunks")
            self.chunks_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in chunk collection : {str(e)}")
            raise

    
    
    
    def ingest_relation(self, chunk_relation_list : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not chunk_relation_list or not all(isinstance(doc, BaseModel) for doc in chunk_relation_list):
                raise ValueError("All chunks needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in chunk_relation_list]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : entity_edges")
            self.entity_edges_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in entity_edges collection : {str(e)}")
            raise

    


    def ingest_chunk_graph(self, chunk_graph : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            documents: List of Pydantic model instances to insert.

        Raises:
            ValueError: If documents is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """

        try:
            if not chunk_graph or not all(isinstance(doc, BaseModel) for doc in chunk_graph):
                raise ValueError("All chunks needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in chunk_graph]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : chunk_edges")
            self.chunk_edges_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in chunk_edges collection : {str(e)}")
            raise


    def create_indexes(self):

        print("Indices Created Started...!")

        self.chunks_collection.create_index("_id")
        self.chunks_collection.create_index("chunk_id")

        self.chunk_edges_collection.create_index("source_chunk")
        self.chunk_edges_collection.create_index("target_chunk")

        self.entity_edges_collection.create_index("chunk_id")

        print("MongoDB Indices Created Successfully..!")


if __name__ == "__main__":

    db = MongoDb()
    db.create_indexes()
