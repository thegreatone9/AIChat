/**
 * Server entry point — starts the Express server.
 */

import app from './app.js';
import config from './config/index.js';
import logger from './utils/logger.js';

// Import database to trigger initialization
import './config/database.js';

const PORT = config.port;

app.listen(PORT, () => {
  logger.info(`AIChat server running on http://localhost:${PORT}`);
  logger.info(`AI service URL: ${config.aiServiceUrl}`);
});
