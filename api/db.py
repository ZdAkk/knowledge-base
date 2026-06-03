import psycopg
from psycopg_pool import AsyncConnectionPool
from config import settings

_pool: AsyncConnectionPool | None = None


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        conninfo = (
            f"host={settings.db_host} port={settings.db_port} "
            f"dbname={settings.db_name} user={settings.db_user} "
            f"password={settings.db_password}"
        )
        _pool = AsyncConnectionPool(conninfo, min_size=2, max_size=10, open=False)
        await _pool.open()
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
