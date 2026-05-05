"""
Diagnostic script — checks ingestion status and retrieval scores.
Run from the ai-services directory with the venv activated:
  python -m app.debug
"""

from app.retrieval.vector_store import search, get_stats
from app.core.config import RELEVANCE_SCORE_THRESHOLD

print("=" * 50)
print("VECTOR STORE STATS")
print("=" * 50)
stats = get_stats()
print(f"  Total chunks: {stats['total_chunks']}")
print(f"  Collection:   {stats['collection_name']}")
print()

if stats["total_chunks"] == 0:
    print("⚠️  No chunks in vector store! The PDF was not ingested properly.")
    exit(1)

query = "what is value?"
print(f"QUERY: \"{query}\"")
print(f"RELEVANCE_SCORE_THRESHOLD: {RELEVANCE_SCORE_THRESHOLD}")
print(f"(scores <= threshold are considered relevant)")
print("=" * 50)

results = search(query, top_k=10)

if not results:
    print("⚠️  No results returned from ChromaDB at all!")
else:
    print(f"\nTop {len(results)} results:\n")
    for i, r in enumerate(results):
        status = "✅ PASS" if r["score"] <= RELEVANCE_SCORE_THRESHOLD else "❌ FILTERED OUT"
        print(f"  [{i+1}] Score: {r['score']:.4f}  {status}")
        print(f"      Doc: {r['metadata'].get('doc_id', '?')[:8]}...")
        print(f"      Text: {r['content'][:120]}...")
        print()

passing = [r for r in results if r["score"] <= RELEVANCE_SCORE_THRESHOLD]
print(f"Chunks passing threshold: {len(passing)} / {len(results)}")

if len(passing) == 0:
    print(f"\n💡 FIX: The threshold ({RELEVANCE_SCORE_THRESHOLD}) is too strict.")
    print(f"   Lowest score was {results[0]['score']:.4f}.")
    print(f"   Recommend raising threshold to ~{min(results[0]['score'] * 1.5, 1.0):.2f}")
