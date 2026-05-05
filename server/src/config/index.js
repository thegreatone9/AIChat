/**
 * Server configuration — reads from environment variables with sensible defaults.
 * Paths are resolved relative to the server directory, not CWD.
 */

import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SERVER_ROOT = path.resolve(__dirname, '..', '..');

const config = {
  port: process.env.PORT || 5000,
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  uploadDir: process.env.UPLOAD_DIR || path.join(SERVER_ROOT, 'uploads'),
  maxFileSize: 100 * 1024 * 1024, // 100 MB
  dbPath: process.env.DB_PATH || path.join(SERVER_ROOT, 'data', 'aichat.db'),
};

export default config;
