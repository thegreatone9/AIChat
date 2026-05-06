# AIChat — AI-Powered Chatbot with Knowledge Handling

An intelligent chatbot that answers questions using only your uploaded documents. Built with a RAG (Retrieval-Augmented Generation) pipeline powered by a locally running LLM — no cloud APIs, no data leaves your machine.

## How It Works

### The Big Picture

```
  You upload a document          You ask a question
  (PDF/TXT/DOCX/MD/CSV/URL)             │
        │                               ▼
        ▼                     ┌─────────────────────────┐
  ┌───────────┐  Extract     │  1. Per-doc vector search │
  │  Upload / │──────────▶  │  2. Keyword fallback     │
  │  Scrape   │   & chunk    │  3. Score gap filter      │
  └───────────┘     │        │  4. Build prompt + history│
                    ▼        │  5. LLM generates answer │
              ┌──────────┐   └────────────┬────────────┘
              │ ChromaDB │                │
              │ (vectors)│◀───────────────┘
              └──────────┘        ▼
                         Answer + Sources (with excerpts)
```

### Document Ingestion

The knowledge base accepts multiple formats:

| Format | How it's extracted |
|---|---|
| **PDF** (`.pdf`) | PyPDF extracts text from all pages |
| **Plain Text** (`.txt`) | Read directly |
| **Markdown** (`.md`) | Read directly |
| **Word** (`.docx`) | python-docx extracts paragraph text |
| **CSV** (`.csv`) | Read as plain text |
| **Web page** (URL) | Fetched with requests, parsed with BeautifulSoup (scripts/nav/footers stripped) |

After extraction:

1. **Chunking** — Text is split into ~500 character chunks with 100 char overlap using LangChain's `RecursiveCharacterTextSplitter`, preserving sentence boundaries
2. **Embedding** — Each chunk is converted to a vector using Ollama's `nomic-embed-text` model
3. **Storage** — Vectors are persisted in ChromaDB with the original text and metadata (doc ID, chunk index)

### Question Answering (RAG Pipeline)

When you ask a question:

1. **Per-Document Vector Search** — Your question is embedded and compared against chunks **from each document individually**, ensuring every document gets representation in the results (see below)
2. **Relevance Filtering** — Only chunks scoring below the distance threshold (0.6) are kept
3. **Score Gap Filter** — Among passing chunks, only those within 1.5× of the best score survive — this ensures you see 1 source when only 1 chunk is relevant, and 5 when 5 are
4. **Keyword Fallback** — If no vector results pass the threshold, keyword matching kicks in as a last resort (see below)
5. **Prompt Construction** — Relevant chunks + the last 5 conversation exchanges are injected into a system prompt
6. **LLM Generation** — Ollama's `qwen2.5:7b` generates the answer with markdown formatting
7. **Source Attribution** — The UI shows collapsible source excerpts with chunk numbers and match percentages

### Per-Document Search (Cross-Document Coverage)

A naive RAG retrieves the top-K most similar chunks globally. This means if you have 2 documents, a broad query like *"List all the people mentioned"* might return all 8 chunks from one document and none from the other.

Our search queries **each document individually** and merges results:

```
  Query: "List all people mentioned"
         │
    ┌────┴────┐
    ▼         ▼
 Doc A       Doc B
 top 4       top 4
 chunks      chunks
    │         │
    └────┬────┘
         ▼
   Merge & sort by score
   Return top 8
```

This guarantees every document in your knowledge base is represented in the context, regardless of how many documents you've uploaded.

### Smart Search: Keyword Fallback

Embedding models are great at semantic similarity (*"What causes inflation?"* matches chunks about *"rising prices"*) but weak at **proper noun matching** (*"Rosa Luxemburg"* may not match a chunk about Rosa Luxemburg if the embedding model doesn't encode the name strongly).

When per-document vector search finds **no results passing the relevance threshold**, a keyword fallback triggers:

```
         ┌──────────────────────────┐
         │  Per-Document Vector     │
         │  Search (semantic)       │
         └────────────┬─────────────┘
                      │
            ┌─────────▼──────────┐
            │ Any results pass   │──── YES ──▶ Return vector results
            │ threshold (0.6)?   │
            └─────────┬──────────┘
                      │ NO
            ┌─────────▼──────────┐
            │  Keyword Search    │──── Found? ──▶ Return keyword results
            │  (exact match,     │
            │   case variants)   │
            └─────────┬──────────┘
                      │ NOT FOUND
                      ▼
              Return "not in KB"
```

- **Vector search** handles ~95% of queries — conceptual, paraphrased, and synonym-based questions
- **Keyword fallback** rescues the ~5% where specific names or proper nouns don't get embedded well
- Keywords are searched with **case variants** (original, lowercase, Title Case) since ChromaDB's `$contains` is case-sensitive

### Conversation Memory

The app remembers the last **5 exchanges** (10 messages) and includes them in every LLM call. This enables:

- **Pronoun resolution** — *"What did she argue?"* after asking about Rosa Luxemburg
- **Follow-up questions** — *"Tell me more about that"*
- **Contextual refinement** — *"What about Yunus?"* after listing people

Memory is session-only (resets on page refresh) and is never stored in the database.

### Graceful Fallback for Unanswerable Questions

The system handles questions it can't answer at two levels:

1. **Retrieval level** — If no chunks pass the relevance threshold (and keyword search also fails), the app returns *"I couldn't find that in the knowledge base"* without ever calling the LLM
2. **LLM level** — If the LLM declines to answer:
   - **Short response** (<200 chars) with fallback phrase → treated as a genuine "can't answer" → sources are stripped
   - **Long response** (200+ chars) with fallback phrase tacked on at the end → the real answer is kept, the trailing disclaimer is stripped

### Markdown Rendering

LLM responses are rendered as rich markdown in the UI — **bold text**, numbered lists, headings, and code blocks all display properly instead of raw asterisks.

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
| **Client** | Vite + React (JS) | Chat UI with markdown rendering, collapsible sources, multi-format upload + URL ingestion |
| **Server** | Node.js + Express | API gateway, file handling (Multer for PDF/TXT/MD/DOCX/CSV), document metadata (SQLite) |
| **AI Services** | Python + FastAPI | Multi-format text extraction, web scraping, chunking, embedding, RAG pipeline with memory |
| **Vector Store** | ChromaDB | Persistent vector storage with per-document cosine similarity search |
| **LLM** | Ollama (local) | `qwen2.5:7b` for generation, `nomic-embed-text` for embeddings |

## Project Structure

```
AIChat/
├── client/                  # Frontend — Vite + React (JS)
│   └── src/
│       ├── components/      # Sidebar, ChatWindow, MessageBubble, ChatInput
│       ├── services/        # API client (api.js)
│       └── index.css        # Design system (dark theme, markdown styles)
├── server/                  # API Gateway — Node.js + Express
│   └── src/
│       ├── config/          # App config (index.js), SQLite init (database.js)
│       ├── controllers/     # Chat (with history) and Knowledge request handlers
│       ├── middleware/      # Global error handler
│       ├── models/          # Document model (SQLite CRUD)
│       ├── routes/          # /api/chat and /api/knowledge routes
│       ├── services/        # HTTP client to AI microservice
│       └── utils/           # Logger
├── ai-services/             # AI Microservice — Python + FastAPI
│   ├── app/
│   │   ├── api/             # /ai/query, /ai/ingest, /ai/ingest-url, /ai/documents
│   │   ├── core/            # Config, RAG chain (prompt + memory + fallback)
│   │   ├── ingestion/       # Multi-format loader (PDF/TXT/MD/DOCX/CSV/URL), text splitter
│   │   ├── retrieval/       # ChromaDB vector store (per-doc search + keyword fallback)
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
| `POST` | `/api/chat` | Send a question with conversation history, get an AI answer with sources |

### Knowledge Base
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/knowledge/upload` | Upload a file — PDF, TXT, MD, DOCX, CSV (max 100MB) |
| `POST` | `/api/knowledge/ingest-url` | Scrape and ingest a web page by URL |
| `GET` | `/api/knowledge/documents` | List all documents |
| `DELETE` | `/api/knowledge/:id` | Delete a document and all its embeddings |

### AI Service (internal)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ai/ingest` | Ingest a file into the vector store |
| `POST` | `/ai/ingest-url` | Fetch and ingest a web page |
| `POST` | `/ai/query` | RAG query with conversation history |
| `DELETE` | `/ai/documents/:id` | Remove document embeddings |
| `GET` | `/ai/health` | Health check with vector store stats |
| `GET` | `/docs` | Auto-generated Swagger documentation |

## License

MIT
