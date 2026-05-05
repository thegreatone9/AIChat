"""
Configuration for the AI services layer.
Centralizes Ollama model names, vector store paths, and RAG parameters.
"""

import os
from pathlib import Path

# --- Ollama ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# --- Vector Store ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
VECTOR_STORE_PATH = os.getenv(
    "VECTOR_STORE_PATH",
    str(BASE_DIR / "data" / "vector_store"),
)
CHROMA_COLLECTION_NAME = "knowledge_base"

# --- Chunking ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# --- Retrieval ---
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RELEVANCE_SCORE_THRESHOLD = float(os.getenv("RELEVANCE_SCORE_THRESHOLD", "0.3"))

# --- Upload ---
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
