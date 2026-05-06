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
2. If the context does not contain enough information, say ONLY:
   "I couldn't find an answer to that in the knowledge base."
3. NEVER combine a real answer with the "couldn't find" message. Either answer the question OR say you couldn't find it — never both.
4. Do NOT make up information or use knowledge outside the provided context.
5. Be concise and direct in your answers.

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


def query(question: str, history: list = None) -> dict:
    """
    Execute the full RAG pipeline:
    1. Search vector store for relevant chunks
    2. Filter by relevance score
    3. Build prompt with context + conversation history
    4. Generate answer via Ollama

    Args:
        question: The user's question.
        history: List of previous messages [{"role": "user"|"assistant", "content": "..."}].

    Returns:
        Dict with 'answer', 'sources', and 'has_context' keys.
    """
    if history is None:
        history = []

    # Step 1: Retrieve relevant chunks
    raw_results = search(question)

    # Step 2: Filter by absolute relevance (cosine distance — lower is better)
    relevant_chunks = [
        r for r in raw_results
        if r["score"] <= RELEVANCE_SCORE_THRESHOLD
    ]

    # Step 2b: Relative score gap — only keep chunks close to the best match.
    if relevant_chunks:
        best_score = relevant_chunks[0]["score"]
        score_cutoff = best_score * 1.5
        relevant_chunks = [
            r for r in relevant_chunks
            if r["score"] <= score_cutoff
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

    # Step 5: Build messages with conversation history and query LLM
    llm = _get_llm()
    messages = [
        ("system", SYSTEM_PROMPT.format(context=context)),
    ]

    # Include last 5 exchanges (10 messages) for conversational context
    recent_history = history[-10:]
    for msg in recent_history:
        role = msg["role"] if isinstance(msg, dict) else msg.role
        content = msg["content"] if isinstance(msg, dict) else msg.content
        messages.append((role if role == "human" else "human" if role == "user" else "ai", content))

    messages.append(("human", question))

    response = llm.invoke(messages)

    # Step 6: Check if the LLM declined to answer
    answer_text = response.content
    fallback_phrases = [
        "couldn't find an answer",
        "could not find an answer",
        "not enough information",
        "don't have enough context",
        "no information available",
    ]
    has_fallback_phrase = any(phrase in answer_text.lower() for phrase in fallback_phrases)

    if has_fallback_phrase:
        # If the answer is short, the LLM genuinely couldn't answer
        if len(answer_text) < 200:
            return {
                "answer": answer_text,
                "sources": [],
                "has_context": False,
            }
        # If the answer is long, the LLM answered but hedged at the end.
        # Strip the trailing fallback sentence and keep the real answer.
        for phrase in fallback_phrases:
            idx = answer_text.lower().find(phrase)
            if idx > 0:
                # Find the start of the sentence containing the fallback
                last_newline = answer_text.rfind('\n', 0, idx)
                last_period = answer_text.rfind('.', 0, idx)
                cut_point = max(last_newline, last_period)
                if cut_point > 0:
                    answer_text = answer_text[:cut_point + 1].strip()
                break

    # Step 7: Collect sources with text excerpts
    sources = []
    for c in relevant_chunks:
        sources.append({
            "doc_id": c["metadata"].get("doc_id", "unknown"),
            "chunk_index": c["metadata"].get("chunk_index", 0),
            "score": round(c["score"], 4),
            "excerpt": c["content"][:300].strip(),
        })

    return {
        "answer": answer_text,
        "sources": sources,
        "has_context": True,
    }
