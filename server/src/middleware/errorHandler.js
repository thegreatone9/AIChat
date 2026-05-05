/**
 * Global error handling middleware.
 */

import logger from '../utils/logger.js';

export function errorHandler(err, req, res, _next) {
  logger.error(`${req.method} ${req.path} — ${err.message}`);

  // Multer file size error
  if (err.code === 'LIMIT_FILE_SIZE') {
    return res.status(413).json({
      error: 'File too large. Maximum size is 100 MB.',
    });
  }

  // Multer file filter error
  if (err.message === 'Only PDF files are allowed.') {
    return res.status(400).json({ error: err.message });
  }

  // Generic server error
  return res.status(err.status || 500).json({
    error: err.message || 'Internal server error.',
  });
}
