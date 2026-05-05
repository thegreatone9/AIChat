/**
 * Document model — SQLite operations for knowledge base document metadata.
 */

import db from '../config/database.js';

const Document = {
  /**
   * Insert a new document record.
   */
  create({ id, filename, fileSize, chunksCount }) {
    const stmt = db.prepare(`
      INSERT INTO documents (id, filename, file_size, chunks_count)
      VALUES (?, ?, ?, ?)
    `);
    return stmt.run(id, filename, fileSize, chunksCount);
  },

  /**
   * Get all documents, ordered by most recent first.
   */
  findAll() {
    return db.prepare('SELECT * FROM documents WHERE status = ? ORDER BY uploaded_at DESC').all('active');
  },

  /**
   * Find a single document by ID.
   */
  findById(id) {
    return db.prepare('SELECT * FROM documents WHERE id = ?').get(id);
  },

  /**
   * Soft-delete a document by marking it inactive.
   */
  delete(id) {
    const stmt = db.prepare('UPDATE documents SET status = ? WHERE id = ?');
    return stmt.run('deleted', id);
  },

  /**
   * Hard-delete a document.
   */
  destroy(id) {
    const stmt = db.prepare('DELETE FROM documents WHERE id = ?');
    return stmt.run(id);
  },
};

export default Document;
