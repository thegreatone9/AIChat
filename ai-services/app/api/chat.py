"""
Chat API routes — query the RAG pipeline.
"""

from fastapi import APIRouter
from app.core.rag_chain import query
from app.schemas.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["chat"])


@router.post("/query", response_model=ChatResponse)
def chat_query(request: ChatRequest):
    """
    Send a question to the RAG pipeline.
    Retrieves relevant context from the knowledge base and generates an answer.
    """
    result = query(request.question, history=request.history)

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        has_context=result["has_context"],
    )
