# AIChat — AI-Powered Chatbot with Knowledge Handling

An intelligent chatbot that answers questions using only your uploaded documents. Built with a RAG (Retrieval-Augmented Generation) pipeline powered by a locally running LLM — no cloud APIs, no data leaves your machine.

## How It Works

### The Big Picture

```
  You upload a PDF               You ask a question
        │                               │
        ▼                               ▼
  ┌───────────┐  Extract    ┌─────────────────────────┐
  │    PDF    │──────────▶ │  1. Search vector store  │
  │  Upload   │   & chunk   │  2. Keyword fallback     │
  └───────────┘     │       │  3. Build prompt         │
                    ▼       │  4. LLM generates answer │
              ┌──────────┐  └────────────┬────────────┘
              │ ChromaDB │               │
              │ (vectors)│◀──────────────┘
              └──────────┘        ▼
                            Answer + Sources
```

### Document Ingestion

When you upload a PDF:

1. **Text Extraction** — PyPDF extracts all text content from the PDF
2. **Chunking** — Text is split into ~500 character chunks with 100 char overlap using LangChain's `RecursiveCharacterTextSplitter`, preserving sentence boundaries
3. **Embedding** — Each chunk is converted to a vector using Ollama's `nomic-embed-text` model
4. **Storage** — Vectors are persisted in ChromaDB with the original text and metadata (doc ID, chunk index)

### Question Answering (RAG Pipeline)

When you ask a question:

1. **Vector Search** — Your question is embedded and compared against all stored chunks using cosine similarity
2. **Relevance Filtering** — Only chunks scoring below the distance threshold (0.6) are kept
3. **Score Gap Filter** — Among passing chunks, only those within 1.5× of the best score survive — this ensures you see 1 source when only 1 chunk is relevant, and 5 when 5 are
4. **Keyword Fallback** — If vector search finds no relevant results (see below), keyword matching kicks in
5. **Prompt Construction** — Relevant chunks are injected into a system prompt that instructs the LLM to answer *only* from the provided context
6. **LLM Generation** — Ollama's `qwen2.5:7b` generates the answer
7. **Source Attribution** — The UI shows which text excerpts were used, with match percentages

### Smart Search: Vector + Keyword Fallback

Embedding models are great at semantic similarity ("What causes inflation?" matches chunks about "rising prices") but weak at **proper noun matching** ("Rosa Luxemburg" won't match a chunk about Rosa Luxemburg if the embedding doesn't encode the name strongly).

Our search uses a **fallback strategy**:

```
         ┌──────────────────┐
         │  Vector Search   │
         │  (semantic)      │
         └────────┬─────────┘
                  │
        ┌─────────▼──────────┐
        │ Do results contain │──── YES ──▶ Return vector results
        │ query keywords?    │
        └─────────┬──────────┘
                  │ NO
        ┌─────────▼──────────┐
        │  Keyword Search    │──── Found? ──▶ Return keyword results
        │  (exact match)     │
        └─────────┬──────────┘
                  │ NOT FOUND
                  ▼
         Return "not in KB"
```

- **Vector search** handles ~95% of queries — conceptual, paraphrased, and synonym-based questions
- **Keyword fallback** rescues the ~5% where specific names, terms, or proper nouns don't get embedded well
- Keywords are searched with **case variants** (original, lowercase, Title Case) since ChromaDB's `$contains` is case-sensitive

### Graceful Fallback for Out-of-Scope Questions

The system handles questions it can't answer at two levels:

1. **Retrieval level** — If no chunks pass the relevance threshold (and keyword search also fails), the app returns a polite "I couldn't find that in the knowledge base" without ever calling the LLM
2. **LLM level** — If chunks are provided but the LLM determines they don't answer the question, it says so — and the app **strips the source references** to avoid showing misleading citations

## Architecture

```
┌────────────────┐       ┌────────────────┐       ┌──────────────────┐
│    Client      │       │    Server      │       │   AI Services    │
│  Vite + React  │──────▶│  Node/Express  │──────▶│  Python/FastAPI  │
│  port 5173     │  API  │  port 5000     │  HTTP │  port 8000       │
└────────────────┘       └───────┬────────┘       └───────┬──────────┘
                                 │                        │
                           ┌─────▼─────┐          ┌───────▼────────┐
                           │  SQLite   │          │   ChromaDB     │
                           │ (metadata)│          │ (vector store) │
                           └───────────┘          └───────┬────────┘
                                                          │
                                                   ┌──────▼──────┐
                                                   │   Ollama    │
                                                   │ qwen2.5:7b  │
                                                   │ nomic-embed │
                                                   └─────────────┘
```

| Layer | Tech | Responsibility |
|---|---|---|
| **Client** | Vite + React (JS) | Chat UI, document sidebar, drag-and-drop upload |
| **Server** | Node.js + Express | API gateway, file handling (Multer), document metadata (SQLite) |
| **AI Services** | Python + FastAPI | PDF extraction, chunking, embedding, RAG pipeline |
| **Vector Store** | ChromaDB | Persistent vector storage with cosine similarity search |
| **LLM** | Ollama (local) | `qwen2.5:7b` for generation, `nomic-embed-text` for embeddings |

## Project Structure

```
AIChat/
├── client/                  # Frontend — Vite + React (JS)
│   └── src/
│       ├── components/      # Sidebar, ChatWindow, MessageBubble, ChatInput
│       ├── services/        # API client (api.js)
│       └── index.css        # Design system (dark theme)
├── server/                  # API Gateway — Node.js + Express
│   └── src/
│       ├── config/          # App config (index.js), SQLite init (database.js)
│       ├── controllers/     # Chat and Knowledge request handlers
│       ├── middleware/      # Global error handler
│       ├── models/          # Document model (SQLite CRUD)
│       ├── routes/          # /api/chat and /api/knowledge routes
│       ├── services/        # HTTP client to AI microservice
│       └── utils/           # Logger
├── ai-services/             # AI Microservice — Python + FastAPI
│   ├── app/
│   │   ├── api/             # /ai/query, /ai/ingest, /ai/documents endpoints
│   │   ├── core/            # Config, RAG chain (prompt + LLM)
│   │   ├── ingestion/       # PDF loader, text splitter
│   │   ├── retrieval/       # ChromaDB vector store (search, add, delete)
│   │   └── schemas/         # Pydantic request/response models
│   └── data/                # Vector store + uploads (gitignored)
├── start.sh                 # Single command to launch everything
├── .env.example             # Environment variable template
└── .gitignore
```

## Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- **Ollama** — [install from ollama.com](https://ollama.com)

### One-Command Setup

```bash
./start.sh
```

That's it. The script will:

1. ✅ Verify Node.js, Python, and Ollama are installed
2. ✅ Pull `qwen2.5:7b` and `nomic-embed-text` models (first run only)
3. ✅ Create Python venv and install dependencies
4. ✅ Install Node.js dependencies for server and client
5. ✅ Kill any existing services on ports 5173/5000/8000
6. ✅ Start all 3 services with live-reload
7. ✅ `Ctrl+C` cleanly shuts everything down

Then open **http://localhost:5173**.

### Manual Setup (if needed)

```bash
# Terminal 1 — AI Services
cd ai-services
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Server
cd server && npm install && npm run dev

# Terminal 3 — Client
cd client && npm install && npm run dev
```

## Configuration

All tuneable parameters are in `ai-services/app/core/config.py`:

| Parameter | Default | What it does |
|---|---|---|
| `LLM_MODEL` | `qwen2.5:7b` | Ollama model for answer generation |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama model for embeddings |
| `CHUNK_SIZE` | `500` | Characters per text chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `8` | Max chunks retrieved per query |
| `RELEVANCE_SCORE_THRESHOLD` | `0.6` | Max cosine distance to consider relevant |

All can be overridden via environment variables.

## API Endpoints

### Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a question, get an AI-generated answer with sources |

### Knowledge Base
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/knowledge/upload` | Upload a PDF (max 100MB) |
| `GET` | `/api/knowledge/documents` | List all documents |
| `DELETE` | `/api/knowledge/:id` | Delete a document and its embeddings |

### AI Service (internal)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ai/ingest` | Ingest a PDF into the vector store |
| `POST` | `/ai/query` | RAG query |
| `DELETE` | `/ai/documents/:id` | Remove document embeddings |
| `GET` | `/ai/health` | Health check with vector store stats |
| `GET` | `/docs` | Auto-generated Swagger documentation |

## License

MIT
