#Connect to MongoDB Instance:
from pymongo import MongoClient, errors
from pymongo.operations import SearchIndexModel
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
MONGO_TOPIC_KNW_HASH = os.getenv("MONGO_TOPIC_KNW_HASH")
MONGO_PROMPT_HASH = os.getenv("MONGO_PROMPT_HASH")
MONGO_TOPIC_PACKET_COL = os.getenv("MONGO_TOPIC_PACKET_COL")
MONGO_QS_BANK_COL = os.getenv("MONGO_QS_BANK_COL")
MONGO_EPISODIC_MEM_COL = os.getenv("MONGO_EPISODIC_MEM_COL")
MONGO_PROCEDURAL_MEM_COL = os.getenv("MONGO_PROCEDURAL_MEM_COL")
MONGO_TEMP_SESSION_MEM_COL = os.getenv("MONGO_TEMP_SESSION_MEM_COL")
MONGO_GLOBAL_BUCKET_COL = os.getenv("MONGO_GLOBAL_BUCKET_COL")


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
        self.topic_knw_hash_collection = self.db[MONGO_TOPIC_KNW_HASH]
        self.prompt_hash_collection = self.db[MONGO_PROMPT_HASH]
        self.topic_packet_collection = self.db[MONGO_TOPIC_PACKET_COL]
        self.qs_bank_collection = self.db[MONGO_QS_BANK_COL]
        self.global_bucket_collection = self.db[MONGO_GLOBAL_BUCKET_COL]

        self.episodic_memory_collection = self.db[MONGO_EPISODIC_MEM_COL]
        self.procedural_memory_collection = self.db[MONGO_PROCEDURAL_MEM_COL]
        self.temp_session_memory_collection = self.db[MONGO_TEMP_SESSION_MEM_COL]

        print(
            f"Connected to MongoDB instance:\n URI: {MONGO_URI}\n Database: {self.db_name}\n "
        )


    def close(self):
        self.db_client.close()

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

        print("Indices Creation Started...!")

        self.chunks_collection.create_index("_id")
        self.chunks_collection.create_index("chunk_id")

        self.chunk_edges_collection.create_index("source_chunk")
        self.chunk_edges_collection.create_index("target_chunk")

        self.entity_edges_collection.create_index("chunk_id")

        self.prompt_hash_collection.create_index(
                                                    [
                                                        ("difficulty", 1),
                                                        ("status", 1),
                                                        ("version", 1),
                                                        ("prompt_id", 1)
                                                    ]
                                                )

        print("MongoDB Indices Created Successfully..!")


    def create_vector_indexes(self):

        print("VECTOR Indices Creation Started...!")
        vector_index = SearchIndexModel(definition={
                                                    'fields' : [
                                                        {
                                                            "type" : "vector",
                                                            "path" : "embeddings",
                                                            "numDimensions" : 3072,
                                                            "similarity" : "cosine"
                                                        },
                                                        {
                                                            "type" : "filter",
                                                            "path" : "document_id"
                                                        }

                                                        ]
                                                    },
                                        name="vector_index",
                                        type="vectorSearch"
                                        )
        
        text_index = SearchIndexModel(
                                        definition={
                                            "mappings": {
                                                "dynamic": False,
                                                "fields": {
                                                        #For Pre-filtering on the document_id field
                                                        "document_id": {
                                                            "type": "token"
                                                        },
                                                        "text": 
                                                            {
                                                                "type": "string"
                                                            },
                                                        
                                                        "entities": 
                                                            {   
                                                                "type": "document",
                                                                "fields": 
                                                                    {
                                                                        "normalized_text": 
                                                                            {
                                                                                "type": "string"
                                                                            }
                                                                    }
                                                            }
                                                    }
                                            }
                                        },
                                        name="text_index",
                                        type="search"
                                    )

        self.chunks_collection.create_search_index(model=vector_index)
        self.chunks_collection.create_search_index(model=text_index)

        print("MongoDB VECTOR Indices Created Successfully..!")

                                    

    def ingest_knowledge_hash(self, knw_hash : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            knw_hash: List of Pydantic model instances to insert.

        Raises:
            ValueError: If knw_hash is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not knw_hash or not all(isinstance(doc, BaseModel) for doc in knw_hash):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in knw_hash]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : topic_knowledge_hash")
            self.topic_knw_hash_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in topic_knowledge_hash collection : {str(e)}")
            raise



    def ingest_prompt_hash(self, prompt_hash : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            prompt_hash: List of Pydantic model instances to insert.

        Raises:
            ValueError: If prompt_hash is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not prompt_hash or not all(isinstance(doc, BaseModel) for doc in prompt_hash):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in prompt_hash]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : prompt_hash_collection")
            self.prompt_hash_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in prompt_hash_collection collection : {str(e)}")
            raise


    def ingest_topic_packet(self, topic_packet : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            topic_packet: List of Pydantic model instances to insert.

        Raises:
            ValueError: If topic_packet is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not topic_packet or not all(isinstance(doc, BaseModel) for doc in topic_packet):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in topic_packet]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : topic_packet")
            self.topic_packet_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in topic_packet collection ") #: {str(e)}
            raise


    def ingest_question_bank(self, qs_bank : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            qs_bank: List of Pydantic model instances to insert.

        Raises:
            ValueError: If qs_bank is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not qs_bank or not all(isinstance(doc, BaseModel) for doc in qs_bank):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in qs_bank]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : question_bank")
            self.qs_bank_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in question_bank collection : {str(e)}")
            raise

    def ingest_memory(self, memory : List[Models], memory_type : str ) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            memory: List of Pydantic model instances to insert.

        Raises:
            ValueError: If memory is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not memory or not all(isinstance(doc, BaseModel) for doc in memory):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in memory]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : {memory_type}")
            if memory_type == "episodic":
                self.episodic_memory_collection.insert_many(db_docs)
            elif memory_type == "procedural":
                self.procedural_memory_collection.insert_many(db_docs)
            else:
                self.temp_session_memory_collection.insert_many(db_docs)
                
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in question_bank collection : {str(e)}")
            raise


    def ingest_global_bucket(self, global_buckets : List[Models]) -> None:
        """Insert multiple documents into the MongoDB collection.

        Args:
            qs_bank: List of Pydantic model instances to insert.

        Raises:
            ValueError: If qs_bank is empty or contains non-Pydantic model items.
            errors.PyMongoError: If the insertion operation fails.
        """
        try:
            if not global_buckets or not all(isinstance(doc, BaseModel) for doc in global_buckets):
                raise ValueError("All documents needs to be pydantic model instances. Please check again.")

            db_docs = [doc.model_dump() for doc in global_buckets]

            for doc in db_docs:
                doc.pop("_id", None)

            print(f"Collection where insertion to happen : global_bucket_collection")
            self.global_bucket_collection.insert_many(db_docs)
            print(f"Inserted {len(db_docs)} documents into MongoDB.")

        except errors.PyMongoError as e:
            print(f"Exception raised while ingesting in global_bucket_collection collection : {str(e)}")
            raise




if __name__ == "__main__":

    db = MongoDb()
    #db.create_indexes()
    #db.create_vector_indexes()
    db.ingest_hash(knw_hash=[])
