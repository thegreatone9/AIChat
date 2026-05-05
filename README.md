# AIChat — AI-Powered Chatbot with Knowledge Handling

An intelligent chatbot that can be trained on a custom knowledge base and responds accurately using RAG (Retrieval-Augmented Generation).

## Architecture

```
┌────────────┐       ┌────────────┐       ┌─────────────────┐
│   Client   │──────▶│   Server   │──────▶│  AI Services    │
│ Vite+React │  API  │  Node.js   │  HTTP │  Python/FastAPI  │
│ :5173      │◀──────│  :5000     │◀──────│  :8000           │
└────────────┘       └─────┬──────┘       └────────┬────────┘
                           │                       │
                      ┌────▼────┐           ┌──────▼───────┐
                      │ MongoDB │           │ Vector Store │
                      └─────────┘           │ (FAISS/Chroma)│
                                            └──────────────┘
```

## Project Structure

```
AIChat/
├── client/                  # Frontend — Vite + React
├── server/                  # Backend API — Node.js + Express
│   └── src/
│       ├── config/          # DB, env, and app configuration
│       ├── controllers/     # Request handlers
│       ├── middleware/      # Auth, logging, error handling
│       ├── models/          # Mongoose schemas
│       ├── routes/          # Express route definitions
│       ├── services/        # Business logic
│       └── utils/           # Helpers and logger
├── ai-services/             # AI microservice — Python + FastAPI
│   ├── app/
│   │   ├── api/             # FastAPI route handlers
│   │   ├── core/            # Config, LLM chain setup
│   │   ├── ingestion/       # Document loaders & chunking
│   │   ├── retrieval/       # Vector search & RAG pipeline
│   │   └── schemas/         # Pydantic models
│   └── data/
│       └── vector_store/    # Persisted embeddings (gitignored)
├── knowledge-base/          # Shared knowledge base assets
│   └── uploads/             # Raw uploaded documents (gitignored)
├── docs/                    # API documentation
├── .env.example             # Environment variable template
└── .gitignore
```

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB

### Setup

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your values

# 2. Frontend
cd client && npm install && npm run dev

# 3. Server
cd server && npm install && npm run dev

# 4. AI Services
cd ai-services && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload
```

## License
MIT
