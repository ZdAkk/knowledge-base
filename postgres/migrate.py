#!/usr/bin/env python3
"""
Migration runner for the knowledge-base database.

Applies any SQL files in postgres/migrations/ that haven't been run yet.
Files are applied in alphabetical order — use a numeric prefix to control order:
    0001_add_books_index.sql
    0002_dreams_schema.sql

Tracks applied migrations in the schema_migrations table (created by 00_extensions.sql).

Usage:
    # From the knowledge-base root:
    python postgres/migrate.py

    # Or via Docker Compose (against the running Postgres container):
    docker compose run --rm -e DB_HOST=postgres api python /app/../postgres/migrate.py

Environment variables (same as the API):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""

import os
import sys
from pathlib import Path
import psycopg


def get_conninfo() -> str:
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'knowledge')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', '')}"
    )


def main():
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found.")
        return

    conn = psycopg.connect(get_conninfo(), autocommit=False)

    try:
        # Ensure tracking table exists (created by 00_extensions.sql, but be safe)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version     text        PRIMARY KEY,
                applied_at  timestamptz DEFAULT now()
            )
        """)
        conn.commit()

        # Get already-applied migrations
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        applied = {r[0] for r in rows}

        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            print("Database is up to date — no migrations to apply.")
            return

        print(f"Applying {len(pending)} migration(s)...\n")

        for migration_file in pending:
            sql = migration_file.read_text(encoding="utf-8")
            print(f"  → {migration_file.name}")

            try:
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (migration_file.name,),
                )
                conn.commit()
                print(f"     ✓ done")
            except Exception as e:
                conn.rollback()
                print(f"     ✗ FAILED: {e}", file=sys.stderr)
                sys.exit(1)

        print(f"\nAll migrations applied successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
