from pathlib import Path

from pydantic import Field
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_file_encoding="utf-8"
    )

    #--------- Status of AgeT ----------
    STATUS : str = "test"

    #--------- LLM Configuration ----------
    MODEL_TYPE : str = "openai"
    MODEL_NAME_QS_GEN : str = "gpt-5.4-mini"
    MODEL_NAME : str = "gpt-4.1-mini"
    MODEL_TEMPERATURE : float = 0.00
    MAX_TOKENS : int = 4000
    MAX_TOKENS_REL_EXTRACTION : int = 1200
    MAX_RETRIES : int = 3
    MODEL_NAME_RERANKER : str = "BAAI/bge-reranker-base"
    RERANKER_K : int = 20
    MODEL_NAME_ENTITY_EXTRACTION : str = "urchade/gliner_medium-v2.1"
    ENTITY_THRESHOLD : float = 0.4
    SPEECH_MODEL_NAME : str = "whisper-large-v3-turbo"

    # --- AgeT Configuration ---
    TOTAL_MESSAGES_SUMMARY_TRIGGER: int = 30
    MAX_TURN_COUNT : int = 5
    MAX_ATTEMPTS : int = 2

    #--------------- EMBEDDING Configuration -------------
    OPENAI_EMBEDDING_MODEL_ID: str = "text-embedding-3-large"
    OPENAI_EMBEDDING_MODEL_DIM: int = 3072
    OLLAMA_EMBEDDING_MODEL_ID: str = "nomic-embed-text"
    ST_EMBEDDING_MODEL_ID: str = "all-mpnet-base-v2"

    # --- RAG Configuration ---
    TOP_K : int = 30 
    RERANK_K : int = 20
    RAG_CHUNK_SIZE: int = 256
    VECTOR_WEIGHT : float = 0.5
    BM25_WEIGHT : float = 0.5 
    CHUNK_EDGE_THRESHOLD : float = 0.72
    QUESTION_SIM_THRESHOLD : float = 0.8

    #---------- Question Generation -------------
    NUM_QUESTIONS : int = 10

    # --- Paths Configuration ---
    #EVALUATION_DATASET_FILE_PATH: Path = Path("data/evaluation_dataset.json")
    #EXTRACTION_METADATA_FILE_PATH: Path = Path("data/extraction_metadata.json")
    GRAPH_PATH : Path = Path(r"aget_api\src\networkx_graphs")
    INTERMITTENT_DATA : Path = Path(r"aget_api\src\intermittent_data")
    RELATION_NORMALIZATION_JSON_PATH : Path = Path(r"aget_api\src\data\relation_normalization.json")
    ENTITY_NORMALIZATION_JSON_PATH : Path = Path(r"aget_api\src\data\entity_normalization.json")
    INITIAL_DATA_SOURCE_PATH : Path = Path(r"aget_api\src\data\data.json")
    TOPIC_NORMALIZATION_JSON_PATH : Path = Path(r"aget_api\src\data\topics.json")
    ENTITY_LABELS_JSON_PATH : Path = Path(r"aget_api\src\data\entity_labels.json") #To DO

    # --- A2A Config ---
    A2A_TRANSPORT : str = "local" #Options : local or http

    # --- MCP STARTUP COMMANDS ---
    MCP_SERVER_COMMAND : str = ""
    MCP_SERVER_ARGS : list[str] = ["python", r"aget_api\src\knowledge_mcp\server.py"]

    # --- Background Jobs --- 
    MAX_CONCURRENCY : int = 4
    REDIS_CONSUMER_MAX_EVENT : int = 10
    REDIS_CONSUMER_BLOCK_SECS : int = 5000



settings = Settings()
