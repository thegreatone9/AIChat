/**
 * Knowledge base controller — handles document upload, listing, and deletion.
 */

import Document from '../models/Document.js';
import { ingestDocument, deleteDocumentEmbeddings } from '../services/aiService.js';
import logger from '../utils/logger.js';

/**
 * POST /api/knowledge/upload
 * Upload a PDF and send it to the AI service for ingestion.
 */
export async function uploadDocument(req, res, next) {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded.' });
    }

    const { originalname, path: filePath, size } = req.file;
    logger.info(`Uploading document: ${originalname} (${(size / 1024 / 1024).toFixed(2)} MB)`);

    // Send to AI service for ingestion
    const aiResult = await ingestDocument(filePath, originalname);

    // Store metadata in SQLite
    Document.create({
      id: aiResult.doc_id,
      filename: originalname,
      fileSize: size,
      chunksCount: aiResult.chunks_added,
    });

    logger.info(`Document ingested: ${originalname} → ${aiResult.chunks_added} chunks`);

    return res.status(201).json({
      id: aiResult.doc_id,
      filename: originalname,
      chunks_count: aiResult.chunks_added,
      message: aiResult.message,
    });
  } catch (error) {
    next(error);
  }
}

/**
 * GET /api/knowledge
 * List all active documents in the knowledge base.
 */
export function listDocuments(req, res, next) {
  try {
    const documents = Document.findAll();
    return res.json({ documents });
  } catch (error) {
    next(error);
  }
}

/**
 * DELETE /api/knowledge/:id
 * Remove a document from both the vector store and metadata DB.
 */
export async function deleteDocument(req, res, next) {
  try {
    const { id } = req.params;

    const doc = Document.findById(id);
    if (!doc) {
      return res.status(404).json({ error: 'Document not found.' });
    }

    // Remove embeddings from AI service
    await deleteDocumentEmbeddings(id);

    // Soft-delete from SQLite
    Document.delete(id);

    logger.info(`Document deleted: ${doc.filename} (${id})`);

    return res.json({
      id,
      message: `Document '${doc.filename}' removed from knowledge base.`,
    });
  } catch (error) {
    next(error);
  }
}
