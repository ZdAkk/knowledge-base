# Adding a New Collection

A "collection" is a domain-specific set of endpoints, a pipeline, and a Postgres schema.
Books is the first. Dreams is the next planned one.

Adding a new collection takes 4 files + a schema.

---

## Step 1: Create the Postgres schema

Add a new init file in `postgres/init/`:

```
postgres/init/02_dreams.sql
```

Follow the same pattern as `01_init.sql`:
- `CREATE SCHEMA IF NOT EXISTS dreams;`
- Create tables with an `embedding vector(3072)` column on the chunks table
- Add a `match_chunks` function for semantic search

> Init files run alphabetically on first container start.
> For an existing database, run manually:
> `docker compose exec postgres psql -U postgres -d knowledge -f /docker-entrypoint-initdb.d/02_dreams.sql`

---

## Step 2: Create the collection module

```
api/collections/dreams/
├── __init__.py
├── models.py       # Pydantic request/response types
├── pipeline.py     # Ingestion logic
└── router.py       # HTTP endpoints
```

### `models.py`
Define request/response shapes specific to this collection.

### `pipeline.py`
Implement ingestion. Use `shared/chunking.py` for text splitting and
`shared/embeddings.py` for vectors — don't reimplement these.

```python
from shared.chunking import chunk_text
from shared.embeddings import embed_batch
```

### `router.py`
```python
router = APIRouter(prefix="/dreams", tags=["dreams"])

@router.post("/ingest", ...)    # accepts whatever input makes sense
@router.get("/search", ...)
@router.get("/list", ...)
```

---

## Step 3: Register the router

In `api/main.py`:

```python
from collections.dreams.router import router as dreams_router
app.include_router(dreams_router)
```

---

## Step 4: Add MCP tools

In `mcp/server.py`:

```python
@mcp.tool()
async def search_dreams(query: str, limit: int = 5) -> str:
    """Semantic search across dream journal entries."""
    ...
```

---

## Conventions

- **One schema per collection** in Postgres (`books`, `dreams`, etc.)
- **Shared code only** in `api/shared/` — chunking and embeddings are reused everywhere
- **Collection logic** stays in `api/collections/<name>/`
- **Router prefix matches collection name**: `/books/...`, `/dreams/...`
- **All text through `chunk_text()`** — consistent cleaning and splitting
- **All embeddings through `shared/embeddings.py`** — one model, one place to swap it

---

## Checklist

- [ ] `postgres/init/0N_<name>.sql` created
- [ ] `api/collections/<name>/` with `__init__.py`, `models.py`, `pipeline.py`, `router.py`
- [ ] Router registered in `api/main.py`
- [ ] MCP tools added in `mcp/server.py`
- [ ] Schema applied to database
- [ ] Tested via `http://localhost:8000/docs`
