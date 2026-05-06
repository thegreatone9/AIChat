/**
 * API client — wraps all fetch calls to the backend server.
 */

const BASE = '/api';

/**
 * Send a chat message and get an AI response.
 */
export async function sendMessage(question, history = []) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Server error: ${res.status}`);
  }

  return res.json();
}

/**
 * Upload a PDF document to the knowledge base.
 */
export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE}/knowledge/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Upload failed: ${res.status}`);
  }

  return res.json();
}

/**
 * List all documents in the knowledge base.
 */
export async function listDocuments() {
  const res = await fetch(`${BASE}/knowledge`);

  if (!res.ok) {
    throw new Error(`Failed to fetch documents: ${res.status}`);
  }

  return res.json();
}

/**
 * Delete a document from the knowledge base.
 */
export async function deleteDocument(id) {
  const res = await fetch(`${BASE}/knowledge/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Delete failed: ${res.status}`);
  }

  return res.json();
}
