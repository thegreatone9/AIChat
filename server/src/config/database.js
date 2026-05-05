/**
 * SQLite database initialization and access.
 * Stores document metadata (id, filename, upload date, chunk count).
 */

import Database from 'better-sqlite3';
import path from 'path';
import fs from 'fs';
import config from './index.js';

// Ensure data directory exists
const dbDir = path.dirname(config.dbPath);
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const db = new Database(config.dbPath);

// Enable WAL mode for better performance
db.pragma('journal_mode = WAL');

// Create documents table if it doesn't exist
db.exec(`
  CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_size INTEGER,
    chunks_count INTEGER DEFAULT 0,
    uploaded_at TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'active'
  )
`);

export default db;
