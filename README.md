# Knowledge Base

Self-hosted RAG system for books and other knowledge collections.
Built on Postgres + pgvector, FastAPI, and an MCP server for direct AI agent access.

## Stack

| Layer | Technology |
|-------|-----------|
| Database | Postgres 16 + pgvector |
| API | FastAPI (Python 3.12) |
| MCP Server | FastMCP (Python) |
| Embeddings | OpenAI `text-embedding-3-large` (3072 dims) |
| Orchestration | Docker Compose |

## Collections

| Name | Status | Description |
|------|--------|-------------|
| `books` | ✅ Active | EPUB ingestion + semantic search |
| `dreams` | 🔜 Planned | Dream journal entries |

## Quick Start

```bash
cp .env.example .env
# Set DB_PASSWORD and OPENAI_API_KEY

docker compose up -d
```

- API + docs: `http://192.168.178.40:8000/docs`
- Postgres: `192.168.178.40:5434`

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full Unraid setup.

## API Endpoints

### Books
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/books/ingest` | Upload an EPUB and ingest it (multipart file) |
| `GET` | `/books/search?q=...` | Semantic search across all books |
| `GET` | `/books/list` | All books with chunk + embedding counts |
| `POST` | `/books/{slug}/embed` | Embed/re-embed a specific book |

### System
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |

## Project Structure

```
knowledge-base/
├── api/
│   ├── main.py                 # App entry, router registration
│   ├── config.py               # Settings from env vars
│   ├── db.py                   # Async Postgres connection pool
│   ├── shared/
│   │   ├── embeddings.py       # OpenAI client (single source of truth)
│   │   └── chunking.py         # Paragraph sliding window + text cleanup
│   └── collections/
│       └── books/              # Books collection
│           ├── router.py       # HTTP endpoints
│           ├── pipeline.py     # EPUB → extract → chunk → ingest → embed
│           └── models.py       # Pydantic types
├── mcp/server.py               # MCP tools for Claude agent access
├── postgres/init/01_init.sql   # Schema bootstrap (runs on first start)
├── docker-compose.yml
├── .env.example
└── docs/
    ├── DEPLOYMENT.md           # Unraid production setup
    ├── DEVELOPMENT.md          # Local dev guide
    └── ADDING_COLLECTIONS.md   # How to add a new collection
```
