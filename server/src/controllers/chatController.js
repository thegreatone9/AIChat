/**
 * Chat controller — handles chat message requests.
 */

import { queryAI } from '../services/aiService.js';
import logger from '../utils/logger.js';

/**
 * POST /api/chat
 * Send a question and get an AI-generated answer from the knowledge base.
 */
export async function sendMessage(req, res, next) {
  try {
    const { question } = req.body;

    if (!question || !question.trim()) {
      return res.status(400).json({ error: 'Question is required.' });
    }

    logger.info(`Chat query: "${question.substring(0, 80)}..."`);

    const result = await queryAI(question.trim());

    return res.json({
      answer: result.answer,
      sources: result.sources || [],
      has_context: result.has_context,
    });
  } catch (error) {
    next(error);
  }
}
