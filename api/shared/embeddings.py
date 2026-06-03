from openai import AsyncOpenAI
from config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def embed(text: str) -> list[float]:
    """Embed a single string. Used for search queries."""
    response = await get_client().embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings. Used during ingestion."""
    response = await get_client().embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    # Results come back in order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
