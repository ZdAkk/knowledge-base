# Deployment Guide (Unraid)

## First-Time Setup

### 1. Copy the project to Unraid

Place the `knowledge-base` folder somewhere on Unraid, e.g. `/mnt/user/appdata/knowledge-base/`.

### 2. Create your `.env`

```bash
cp .env.example .env
```

Fill in:
```env
DB_PASSWORD=<strong password>
OPENAI_API_KEY=sk-...
```

Leave `DB_HOST=postgres` — inside Docker Compose, services reference each other by name.

### 3. Start the stack

```bash
docker compose up -d
```

Docker will:
1. Pull `pgvector/pgvector:pg16`
2. Build the `api` and `mcp` images
3. Run `postgres/init/01_init.sql` on first start (creates schema + pgvector extension)
4. Start all three services

Verify:
```bash
docker compose ps
docker compose logs api
```

### 4. Confirm the API is reachable

```
http://192.168.178.40:8000/health   → {"status": "ok"}
http://192.168.178.40:8000/docs     → interactive API docs
```

---

## Ingesting Books

Send the EPUB file directly to the API — no server-side folder needed:

```bash
curl -X POST http://192.168.178.40:8000/books/ingest \
  -F "file=@/path/to/atomic-habits.epub"
```

Or via a Trigger.dev automation that watches a folder/source and POSTs the file automatically.

---

## Connecting Claude Code (MCP)

Add to `C:\Users\zaid\AppData\Roaming\Claude\claude_desktop_config.json`:

```json
"knowledge-base": {
  "type": "sse",
  "url": "http://192.168.178.40:3000/sse"
}
```

No local Docker needed — Claude connects directly to the running MCP server over SSE.

---

## Updating the Stack

```bash
docker compose build        # rebuild changed images
docker compose up -d        # restart with new images
```

If the Postgres schema changed, run migrations manually:
```bash
docker compose exec postgres psql -U postgres -d knowledge
```

---

## Data Persistence

Postgres data is stored at `/mnt/cache/appdata/knowledge-base-postgres/` on Unraid,
bind-mounted directly to `/var/lib/postgresql/data`. Data survives container recreation
and reboots.

Backup:
```bash
docker compose exec postgres pg_dump -U postgres knowledge > backup.sql
```

---

## Ports

| Service | Host binding | Purpose |
|---------|-------------|---------|
| API | `192.168.178.40:8000` | REST API (local network only) |
| Postgres | `192.168.178.40:5434` | Direct DB access (local network only) |
| MCP | `3000` | Internal only |
