/**
 * HTTP client for communicating with the Python AI microservice.
 * Uses native Node.js 18+ fetch, FormData, and Blob (no node-fetch needed).
 */

import fs from 'fs';
import config from '../config/index.js';
import logger from '../utils/logger.js';

const AI_BASE = config.aiServiceUrl;

/**
 * Send a chat query to the AI service.
 */
export async function queryAI(question, history = []) {
  const res = await fetch(`${AI_BASE}/ai/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history }),
  });

  if (!res.ok) {
    const error = await res.text();
    logger.error(`AI query failed: ${res.status} — ${error}`);
    throw new Error(`AI service error: ${res.status}`);
  }

  return res.json();
}

/**
 * Send a file to the AI service for ingestion.
 * Reads the file from disk and re-uploads it as multipart/form-data.
 */
export async function ingestDocument(filePath, filename) {
  const fileBuffer = fs.readFileSync(filePath);
  const blob = new Blob([fileBuffer], { type: 'application/pdf' });

  const formData = new FormData();
  formData.append('file', blob, filename);

  const res = await fetch(`${AI_BASE}/ai/ingest`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const error = await res.text();
    logger.error(`AI ingestion failed: ${res.status} — ${error}`);
    throw new Error(`AI ingestion error: ${res.status}`);
  }

  return res.json();
}

/**
 * Delete a document's embeddings from the AI service.
 */
export async function deleteDocumentEmbeddings(docId) {
  const res = await fetch(`${AI_BASE}/ai/documents/${docId}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const error = await res.text();
    logger.error(`AI delete failed: ${res.status} — ${error}`);
    throw new Error(`AI delete error: ${res.status}`);
  }

  return res.json();
}

/**
 * Check AI service health.
 */
export async function healthCheck() {
  const res = await fetch(`${AI_BASE}/ai/health`);
  return res.json();
}
