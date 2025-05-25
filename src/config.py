# config.py
import os

# Weaviate configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

# Ollama configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3:8b")
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096

# Document processing
CHUNK_SIZE = 1024
CHUNK_OVERLAP = 128

# Metadata collection name
METADATA_COLLECTION = "DocumentMetadata"