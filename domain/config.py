# domain/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# File Paths
PDF_PATH = "PEATA.pdf"
VECTOR_DB_PATH = "faiss_index"

# Model Configs
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL = "claude-sonnet-4-5-20250929"

# Chunking Config
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 500

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
