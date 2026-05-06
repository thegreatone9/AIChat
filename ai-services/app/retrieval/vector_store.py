"""
ChromaDB vector store management.
Handles initialization, adding documents, searching, and deleting.
"""

import chromadb
from langchain_ollama import OllamaEmbeddings
from app.core.config import (
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
    VECTOR_STORE_PATH,
    CHROMA_COLLECTION_NAME,
    RETRIEVAL_TOP_K,
)

# Module-level singletons (initialized lazily)
_client = None
_collection = None
_embeddings = None


def _get_embeddings():
    """Get or create the Ollama embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OllamaEmbeddings(
            model=EMBEDDING_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    return _embeddings


def _get_collection():
    """Get or create the ChromaDB collection."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
        _collection = _client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_documents(chunks: list[dict]) -> int:
    """
    Add document chunks to the vector store.

    Args:
        chunks: List of dicts with 'content' and 'metadata' keys.

    Returns:
        Number of chunks added.
    """
    if not chunks:
        return 0

    collection = _get_collection()
    embeddings = _get_embeddings()

    contents = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"{c['metadata']['doc_id']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]

    # Generate embeddings
    vectors = embeddings.embed_documents(contents)

    collection.add(
        ids=ids,
        documents=contents,
        metadatas=metadatas,
        embeddings=vectors,
    )

    return len(chunks)


def search(query: str, top_k: int = RETRIEVAL_TOP_K) -> list[dict]:
    """
    Search with keyword fallback.

    1. Try vector similarity search first.
    2. If no results pass the relevance threshold, fall back to keyword
       search in ChromaDB for proper nouns and specific terms.

    Args:
        query: User question.
        top_k: Number of results to return.

    Returns:
        List of dicts with 'content', 'metadata', and 'score' keys.
        Scores are cosine distances (lower = more similar).
    """
    collection = _get_collection()
    embeddings = _get_embeddings()

    # --- 1. Per-document vector search ---
    # Query each document separately so every document gets representation.
    # This prevents broad queries from only returning chunks from one doc.
    query_vector = embeddings.embed_query(query)

    # Get all unique doc_ids in the collection
    all_meta = collection.get(include=["metadatas"])
    doc_ids = list({m["doc_id"] for m in all_meta["metadatas"] if "doc_id" in m})

    if not doc_ids:
        return []

    # Query each document for its best chunks
    chunks_per_doc = max(2, top_k // len(doc_ids))  # at least 2 per doc
    hits = []

    for doc_id in doc_ids:
        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=chunks_per_doc,
                where={"doc_id": doc_id},
                include=["documents", "metadatas", "distances"],
            )

            if results and results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    hits.append({
                        "content": doc,
                        "metadata": meta,
                        "score": dist,
                    })
        except Exception:
            continue

    # Sort all hits by score and return top_k
    hits.sort(key=lambda h: h["score"])
    hits = hits[:top_k]

    # Check if vector search found anything useful
    from app.core.config import RELEVANCE_SCORE_THRESHOLD
    passing_hits = [h for h in hits if h["score"] <= RELEVANCE_SCORE_THRESHOLD]

    if passing_hits:
        return hits

    # --- 2. Fallback: keyword search ---
    # Vector search failed — try exact keyword matching.
    # Extract significant words (4+ chars, skip common words).
    stop_words = {
        "what", "does", "how", "why", "who", "when", "where", "which",
        "the", "is", "are", "was", "were", "been", "being", "have", "has",
        "had", "did", "will", "would", "could", "should", "can", "may",
        "about", "from", "with", "that", "this", "for", "and", "but",
        "not", "they", "them", "their", "its", "into", "also", "than",
        "then", "more", "most", "such", "like", "argue", "between",
    }
    words = [w.strip("?.,!\"'()") for w in query.split() if len(w) >= 4]
    keywords = [w for w in words if w.lower() not in stop_words]

    if not keywords:
        return hits  # nothing to search for

    # Search each keyword with case variants (ChromaDB $contains is case-sensitive)
    seen_ids = set()
    keyword_hits = []

    for kw in keywords:
        for variant in {kw, kw.lower(), kw.capitalize()}:
            try:
                kw_results = collection.get(
                    where_document={"$contains": variant},
                    include=["documents", "metadatas"],
                    limit=top_k,
                )
                if kw_results and kw_results["ids"]:
                    for cid, doc, meta in zip(
                        kw_results["ids"],
                        kw_results["documents"],
                        kw_results["metadatas"],
                    ):
                        if cid not in seen_ids:
                            seen_ids.add(cid)
                            keyword_hits.append({
                                "content": doc,
                                "metadata": meta,
                                "score": 0.30,  # good enough to pass threshold
                            })
            except Exception:
                continue

    return keyword_hits[:top_k] if keyword_hits else hits


def delete_by_doc_id(doc_id: str) -> int:
    """
    Remove all chunks belonging to a specific document.

    Args:
        doc_id: The document identifier.

    Returns:
        Number of chunks deleted.
    """
    collection = _get_collection()

    # Find all chunk IDs for this document
    existing = collection.get(
        where={"doc_id": doc_id},
        include=[],
    )

    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
        return len(existing["ids"])

    return 0


def get_stats() -> dict:
    """Return basic stats about the vector store."""
    collection = _get_collection()
    return {
        "total_chunks": collection.count(),
        "collection_name": CHROMA_COLLECTION_NAME,
    }
