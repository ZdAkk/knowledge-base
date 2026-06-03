# Postgres

## Directory Structure

```
postgres/
├── init/               # Runs automatically on first container start (alphabetical order)
│   ├── 00_extensions.sql   # pgvector extension + schema_migrations tracking table
│   ├── 01_books.sql        # books schema
│   └── 02_dreams.sql       # dreams schema (add when ready)
├── migrations/         # Changes to existing schemas after first deploy
│   └── 0001_example.sql
└── migrate.py          # Migration runner script
```

## Init vs Migrations

| | `init/` | `migrations/` |
|---|---|---|
| When it runs | Once, on first container start | Manually, via `migrate.py` |
| Purpose | Create schemas from scratch | Alter existing schemas |
| Format | Plain SQL | Plain SQL |
| Tracked | No | Yes, in `schema_migrations` table |

**Rule of thumb:** If you're adding a new collection, add a file to `init/`.
If you're changing an existing schema (adding a column, new index, etc.), add a file to `migrations/`.

## Running Migrations

```bash
# Against local dev Postgres
DB_HOST=localhost DB_PORT=5434 DB_PASSWORD=devpassword python postgres/migrate.py

# Against the running Docker container
docker compose exec api python /postgres/migrate.py
```

## Adding a Migration

Create a new file in `migrations/` with a numeric prefix:
```
migrations/0001_add_books_language_index.sql
migrations/0002_dreams_schema.sql
```

The runner applies files in alphabetical order and skips anything already in `schema_migrations`.

## Adding a New Collection

1. Create `postgres/init/0N_<collection>.sql` with the full schema
2. Apply it manually on existing databases: `docker compose exec postgres psql -U postgres -d knowledge -f /docker-entrypoint-initdb.d/0N_<collection>.sql`
