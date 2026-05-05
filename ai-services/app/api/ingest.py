"""
Ingestion API routes — upload and process documents.
"""

import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import UPLOAD_DIR
from app.ingestion.loader import load_pdf
from app.ingestion.splitter import split_text
from app.retrieval.vector_store import add_documents, delete_by_doc_id
from app.schemas.models import IngestResponse, DeleteResponse

router = APIRouter(prefix="/ai", tags=["ingestion"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_document(file: UploadFile = File(...)):
    """
    Upload and ingest a PDF document into the knowledge base.
    Extracts text, chunks it, generates embeddings, and stores in ChromaDB.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

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

    # Extract text from PDF
    try:
        text = load_pdf(str(file_path))
    except Exception as e:
        # Clean up saved file on failure
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to extract text from PDF: {str(e)}")

    if not text.strip():
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="PDF appears to contain no extractable text.")

    # Chunk the text
    chunks = split_text(text, doc_id)

    # Add to vector store
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
