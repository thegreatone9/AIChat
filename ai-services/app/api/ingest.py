"""
Ingestion API routes — upload files and ingest web pages into the knowledge base.
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from app.core.config import UPLOAD_DIR
from app.ingestion.loader import load_file, load_url, SUPPORTED_EXTENSIONS
from app.ingestion.splitter import split_text
from app.retrieval.vector_store import add_documents, delete_by_doc_id
from app.schemas.models import IngestResponse, DeleteResponse

router = APIRouter(prefix="/ai", tags=["ingestion"])


# --- File Upload ---

@router.post("/ingest", response_model=IngestResponse)
def ingest_document(file: UploadFile = File(...)):
    """
    Upload and ingest a document into the knowledge base.
    Supports: PDF, TXT, Markdown, DOCX, CSV.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Validate file type
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Generate unique document ID
    doc_id = str(uuid.uuid4())
    filename = file.filename

    # Save uploaded file
    file_path = UPLOAD_DIR / f"{doc_id}_{filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Extract text
    try:
        text = load_file(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to extract text: {str(e)}")

    if not text.strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Document appears to contain no extractable text.")

    # Chunk and store
    chunks = split_text(text, doc_id)

    try:
        chunks_added = add_documents(chunks)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings: {str(e)}")

    return IngestResponse(
        doc_id=doc_id,
        filename=filename,
        chunks_added=chunks_added,
        message=f"Successfully ingested '{filename}' — {chunks_added} chunks stored.",
    )


# --- URL Ingestion ---

class UrlIngestRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)


@router.post("/ingest-url", response_model=IngestResponse)
def ingest_url(request: UrlIngestRequest):
    """
    Fetch a web page and ingest its text content into the knowledge base.
    """
    url = request.url.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    doc_id = str(uuid.uuid4())

    # Extract the domain + path for the display name
    from urllib.parse import urlparse
    parsed = urlparse(url)
    display_name = f"{parsed.netloc}{parsed.path[:40]}"
    if len(parsed.path) > 40:
        display_name += "..."

    # Fetch and extract text
    try:
        text = load_url(url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to fetch URL: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="Web page appears to contain no extractable text.")

    # Save the raw text for reference
    file_path = UPLOAD_DIR / f"{doc_id}_{display_name.replace('/', '_')}.txt"
    file_path.write_text(text, encoding="utf-8")

    # Chunk and store
    chunks = split_text(text, doc_id)

    try:
        chunks_added = add_documents(chunks)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Failed to store embeddings: {str(e)}")

    return IngestResponse(
        doc_id=doc_id,
        filename=display_name,
        chunks_added=chunks_added,
        message=f"Successfully ingested '{display_name}' — {chunks_added} chunks stored.",
    )


# --- Delete ---

@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
def delete_document(doc_id: str):
    """
    Remove all embeddings for a specific document from the vector store.
    """
    chunks_deleted = delete_by_doc_id(doc_id)

    # Also remove the uploaded file if it exists
    for f in UPLOAD_DIR.iterdir():
        if f.name.startswith(doc_id):
            f.unlink(missing_ok=True)
            break

    return DeleteResponse(
        doc_id=doc_id,
        chunks_deleted=chunks_deleted,
        message=f"Deleted {chunks_deleted} chunks for document {doc_id}.",
    )
