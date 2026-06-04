from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import get_pool, close_pool
from routers.books.router import router as books_router
from routers.dreams.router import router as dreams_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open DB pool
    await get_pool()
    yield
    # Shutdown: close DB pool
    await close_pool()


app = FastAPI(
    title="Knowledge Base API",
    description="Modular RAG API for books, dreams, and other knowledge collections.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers — add new collections here
app.include_router(books_router)
app.include_router(dreams_router)


@app.get("/health")
async def health():
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute("SELECT 1")
    return {"status": "ok"}
