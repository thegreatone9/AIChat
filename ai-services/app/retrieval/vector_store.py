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
    Search the vector store for chunks relevant to the query.

    Args:
        query: User question.
        top_k: Number of results to return.

    Returns:
        List of dicts with 'content', 'metadata', and 'score' keys.
        Scores are cosine distances (lower = more similar).
    """
    collection = _get_collection()
    embeddings = _get_embeddings()

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
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

    return hits


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
