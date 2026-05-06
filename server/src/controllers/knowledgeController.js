/**
 * Knowledge base controller — handles document upload, URL ingestion, listing, and deletion.
 */

import Document from '../models/Document.js';
import { ingestDocument, ingestUrlContent, deleteDocumentEmbeddings } from '../services/aiService.js';
import logger from '../utils/logger.js';

/**
 * POST /api/knowledge/upload
 * Upload a file and send it to the AI service for ingestion.
 * Supports: PDF, TXT, Markdown, DOCX, CSV.
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
 * POST /api/knowledge/ingest-url
 * Fetch a web page and ingest its text content into the knowledge base.
 */
export async function ingestUrl(req, res, next) {
  try {
    const { url } = req.body;

    if (!url || !url.trim()) {
      return res.status(400).json({ error: 'URL is required.' });
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return res.status(400).json({ error: 'URL must start with http:// or https://' });
    }

    logger.info(`Ingesting URL: ${url}`);

    const aiResult = await ingestUrlContent(url.trim());

    // Store metadata in SQLite
    Document.create({
      id: aiResult.doc_id,
      filename: aiResult.filename,
      fileSize: 0,
      chunksCount: aiResult.chunks_added,
    });

    logger.info(`URL ingested: ${aiResult.filename} → ${aiResult.chunks_added} chunks`);

    return res.status(201).json({
      id: aiResult.doc_id,
      filename: aiResult.filename,
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
