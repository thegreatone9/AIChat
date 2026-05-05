"""
Text chunking using LangChain's RecursiveCharacterTextSplitter.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def split_text(text: str, doc_id: str) -> list[dict]:
    """
    Split a large text into overlapping chunks with metadata.

    Args:
        text: The full document text.
        doc_id: Unique identifier for the source document.

    Returns:
        List of dicts with 'content' and 'metadata' keys.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_text(text)

    return [
        {
            "content": chunk,
            "metadata": {
                "doc_id": doc_id,
                "chunk_index": i,
            },
        }
        for i, chunk in enumerate(chunks)
    ]
