"""
RAG chain: retrieves relevant context from the vector store,
then generates an answer using Ollama's LLM.
"""

from langchain_ollama import ChatOllama
from app.core.config import (
    OLLAMA_BASE_URL,
    LLM_MODEL,
    RELEVANCE_SCORE_THRESHOLD,
)
from app.retrieval.vector_store import search

# System prompt instructs the LLM to only answer from provided context
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based ONLY on the provided context.

Rules:
1. Answer the question using ONLY the information in the context below.
2. If the context does not contain enough information to answer the question, respond with:
   "I couldn't find an answer to that in the knowledge base. Could you try rephrasing your question or asking about a different topic?"
3. Do NOT make up information or use knowledge outside the provided context.
4. Be concise and direct in your answers.
5. If relevant, mention which part of the knowledge base your answer comes from.

Context:
{context}
"""

# Lazy singleton
_llm = None


def _get_llm():
    """Get or create the Ollama LLM instance."""
    global _llm
    if _llm is None:
        _llm = ChatOllama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
        )
    return _llm


def query(question: str) -> dict:
    """
    Execute the full RAG pipeline:
    1. Search vector store for relevant chunks
    2. Filter by relevance score
    3. Build prompt with context
    4. Generate answer via Ollama

    Args:
        question: The user's question.

    Returns:
        Dict with 'answer', 'sources', and 'has_context' keys.
    """
    # Step 1: Retrieve relevant chunks
    raw_results = search(question)

    # Step 2: Filter by relevance (cosine distance — lower is better)
    relevant_chunks = [
        r for r in raw_results
        if r["score"] <= RELEVANCE_SCORE_THRESHOLD
    ]

    # Step 3: Handle no relevant context
    if not relevant_chunks:
        return {
            "answer": (
                "I couldn't find an answer to that in the knowledge base. "
                "Could you try rephrasing your question or asking about "
                "a different topic?"
            ),
            "sources": [],
            "has_context": False,
        }

    # Step 4: Build context string from relevant chunks
    context = "\n\n---\n\n".join([c["content"] for c in relevant_chunks])

    # Step 5: Build messages and query LLM
    llm = _get_llm()
    messages = [
        ("system", SYSTEM_PROMPT.format(context=context)),
        ("human", question),
    ]

    response = llm.invoke(messages)

    # Step 6: Collect source metadata
    sources = []
    seen_docs = set()
    for c in relevant_chunks:
        doc_id = c["metadata"].get("doc_id", "unknown")
        if doc_id not in seen_docs:
            seen_docs.add(doc_id)
            sources.append({
                "doc_id": doc_id,
                "score": round(c["score"], 4),
            })

    return {
        "answer": response.content,
        "sources": sources,
        "has_context": True,
    }
