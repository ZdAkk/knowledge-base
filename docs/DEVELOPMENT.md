# Development Guide

## Prerequisites

- Python 3.12+
- Docker Desktop
- An OpenAI API key

## Local Setup

### 1. Clone and configure

```bash
cd knowledge-base
cp .env.example .env
```

Edit `.env`:
```env
DB_HOST=localhost        # Override for local dev
DB_PORT=5434             # Match the exposed port below
DB_NAME=knowledge
DB_USER=postgres
DB_PASSWORD=devpassword

OPENAI_API_KEY=sk-...
```

### 2. Start only the database

For local development, run only Postgres in Docker while running the API directly:

```bash
docker compose up postgres -d
```

Postgres will be available at `localhost:5434`.

### 3. Set up Python environment

```bash
cd api
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 4. Run the API

```bash
cd api
uvicorn main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs` — use these to test endpoints interactively.
To test ingestion, upload an EPUB via the `/books/ingest` endpoint in the docs UI.

### 5. Run the MCP server (optional)

```bash
cd mcp
pip install -r requirements.txt
API_BASE_URL=http://localhost:8000 python server.py
```

---

## Making Changes

### API changes
FastAPI reloads automatically with `--reload`. No Docker rebuild needed during development.

### Schema changes
Init scripts only run on a **fresh** database. For an existing dev DB:
- Run the SQL manually via psql or a DB client, or
- Wipe and recreate: `docker compose down -v && docker compose up postgres -d`

### Dependency changes
After editing `api/requirements.txt`:
```bash
pip install -r requirements.txt        # local dev
docker compose build api               # rebuild Docker image
```

---

## Running Tests

```bash
cd api
pytest
```

No tests yet — put them in `api/tests/` following the `test_<module>.py` convention.

---

## Code Style

- Python: PEP 8, type hints everywhere
- All async — no sync DB or HTTP calls
- Pydantic models for all request/response shapes (in each collection's `models.py`)
- No business logic in `router.py` — delegate to `pipeline.py`

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | `postgres` | Postgres hostname |
| `DB_PORT` | Yes | `5432` | Postgres port |
| `DB_NAME` | Yes | `knowledge` | Database name |
| `DB_USER` | Yes | `postgres` | DB username |
| `DB_PASSWORD` | Yes | — | DB password |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for embeddings |
| `EMBEDDING_MODEL` | No | `text-embedding-3-large` | OpenAI embedding model |
| `EMBEDDING_DIMS` | No | `3072` | Embedding dimensions |
