"""
Knowledge Base MCP Server

Exposes the knowledge base API as MCP tools so Claude can
search and inspect the database directly in any session.
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")

mcp = FastMCP("knowledge-base")


# ─── Books ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_books(query: str, limit: int = 5, threshold: float = 0.3) -> str:
    """
    Semantic search across all ingested books.
    Returns the most relevant passages with book title, chapter, and similarity score.

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 5)
        threshold: Minimum similarity score 0–1 (default 0.3, lower = more results)
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_BASE}/books/search",
            params={"q": query, "limit": limit, "threshold": threshold},
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return f"No results found for: '{query}'"

    lines = [f"Search results for: '{query}'\n"]
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. [{r['title']}] — {r['chapter_title']} (similarity: {r['similarity']:.3f})\n"
            f"   {r['text'][:400]}{'...' if len(r['text']) > 400 else ''}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def list_books() -> str:
    """
    List all books in the knowledge base with chunk and embedding counts.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_BASE}/books/list")
        resp.raise_for_status()
        books = resp.json()

    if not books:
        return "No books in the knowledge base yet."

    lines = ["Books in knowledge base:\n"]
    for b in books:
        embedded = b["embedded_chunks"]
        total = b["total_chunks"]
        if embedded == total and total > 0:
            status = f"✓ {total} chunks"
        else:
            status = f"⚠ {embedded}/{total} chunks embedded"
        lines.append(f"  • {b['title']} — {b['author'] or 'Unknown'} [{status}]")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=3000)
