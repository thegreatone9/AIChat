/**
 * Knowledge base routes — upload files, ingest URLs, list, and delete documents.
 */

import { Router } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import config from '../config/index.js';
import {
  uploadDocument,
  ingestUrl,
  listDocuments,
  deleteDocument,
} from '../controllers/knowledgeController.js';

// Ensure upload directory exists
if (!fs.existsSync(config.uploadDir)) {
  fs.mkdirSync(config.uploadDir, { recursive: true });
}

// Supported file extensions
const ALLOWED_EXTENSIONS = new Set(['.pdf', '.txt', '.md', '.docx', '.csv']);

// Multer config — save uploaded files to disk
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, config.uploadDir),
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${file.originalname}`;
    cb(null, uniqueName);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: config.maxFileSize },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      return cb(new Error(`Unsupported file type '${ext}'. Supported: ${[...ALLOWED_EXTENSIONS].join(', ')}`));
    }
    cb(null, true);
  },
});

const router = Router();

router.post('/upload', upload.single('file'), uploadDocument);
router.post('/ingest-url', ingestUrl);
router.get('/', listDocuments);
router.delete('/:id', deleteDocument);

export default router;
