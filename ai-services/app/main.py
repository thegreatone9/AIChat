"""
FastAPI application entry point for the AI services layer.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.retrieval.vector_store import get_stats
from app.schemas.models import HealthResponse

app = FastAPI(
    title="AIChat — AI Services",
    description="RAG-based AI microservice for knowledge base querying",
    version="1.0.0",
)

# CORS — allow the Node server to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/ai/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint with vector store stats."""
    stats = get_stats()
    return HealthResponse(
        status="ok",
        total_chunks=stats["total_chunks"],
        collection_name=stats["collection_name"],
    )


@app.get("/", tags=["health"])
async def root():
    return {"message": "AIChat AI Services is running. Visit /docs for API documentation."}
