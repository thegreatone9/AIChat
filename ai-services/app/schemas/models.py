"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field


# --- Chat ---

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class SourceInfo(BaseModel):
    doc_id: str
    chunk_index: int
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo] = []
    has_context: bool


# --- Ingestion ---

class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    chunks_added: int
    message: str


# --- Delete ---

class DeleteResponse(BaseModel):
    doc_id: str
    chunks_deleted: int
    message: str


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    total_chunks: int
    collection_name: str
