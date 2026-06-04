"""
Knowledge Base MCP Server

Exposes the knowledge base API as MCP tools so Claude can
search and inspect books and dreams directly in any session.
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.getenv("API_BASE_URL", "http://api:8000")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")

mcp = FastMCP("knowledge-base", host="0.0.0.0", port=3000)


def _headers() -> dict:
    """Auth headers for every API request."""
    return {"Authorization": f"Bearer {API_SECRET_KEY}"}


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
            headers=_headers(),
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
        resp = await client.get(f"{API_BASE}/books/list", headers=_headers())
        resp.raise_for_status()
        books = resp.json()

    if not books:
        return "No books in the knowledge base yet."

    lines = ["Books in knowledge base:\n"]
    for b in books:
        embedded = b["embedded_chunks"]
        total = b["total_chunks"]
        status = f"✓ {total} chunks" if embedded == total and total > 0 else f"⚠ {embedded}/{total} chunks embedded"
        lines.append(f"  • {b['title']} — {b['author'] or 'Unknown'} [{status}]")
    return "\n".join(lines)


# ─── Dreams ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_dreams(
    query: str,
    limit: int = 5,
    threshold: float = 0.3,
    source_type: str | None = None,
) -> str:
    """
    Semantic search across all dream records.
    Can search within specific parts of the dream record.

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 5)
        threshold: Minimum similarity score 0–1 (default 0.3)
        source_type: Optional filter — one of: cleaned_dream, jungian_analysis,
                     waking_life, symbol. Leave empty to search everything.
    """
    params: dict = {"q": query, "limit": limit, "threshold": threshold}
    if source_type:
        params["source_type"] = source_type

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_BASE}/dreams/search",
            params=params,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return f"No dream records found for: '{query}'"

    lines = [f"Dream search results for: '{query}'\n"]
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. [{r['dreamed_on']}] {r['title'] or 'Untitled'} "
            f"— {r['source_type']} (similarity: {r['similarity']:.3f})\n"
            f"   {r['text'][:400]}{'...' if len(r['text']) > 400 else ''}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def list_dreams(limit: int = 20) -> str:
    """
    List all recorded dreams, newest first.

    Args:
        limit: Maximum number of dreams to return (default 20)
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{API_BASE}/dreams/list",
            params={"limit": limit},
            headers=_headers(),
        )
        resp.raise_for_status()
        dreams = resp.json()

    if not dreams:
        return "No dreams recorded yet."

    lines = ["Recorded dreams:\n"]
    for d in dreams:
        tone = ", ".join(d["emotional_tone"]) if d.get("emotional_tone") else "—"
        interpreted = "✓ interpreted" if d["has_interpretation"] else "⏳ pending"
        lines.append(
            f"  • [{d['dreamed_on']}] {d['title'] or 'Untitled'} "
            f"| tone: {tone} | {interpreted} | id: {d['dream_id']}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_dream(dream_id: str) -> str:
    """
    Get the full record for a specific dream including symbols and Jungian interpretation.

    Args:
        dream_id: The dream's UUID
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_BASE}/dreams/{dream_id}", headers=_headers())
        if resp.status_code == 404:
            return f"Dream {dream_id} not found."
        resp.raise_for_status()
        d = resp.json()

    lines = [
        f"Dream — {d['dreamed_on']}",
        f"Title: {d['title'] or 'Untitled'}",
        f"Tone: {', '.join(d['emotional_tone']) if d.get('emotional_tone') else '—'}",
        f"Lucid: {'Yes' if d['lucid'] else 'No'}",
        "",
        "── Raw Dream ──",
        d["raw_text"],
    ]

    if d.get("cleaned_text"):
        lines += ["", "── Cleaned ──", d["cleaned_text"]]

    if d.get("symbols"):
        lines += ["", "── Symbols ──"]
        for s in d["symbols"]:
            lines.append(f"  • {s['name']} — {s['archetype'] or '?'}: {s['significance'] or ''}")

    if d.get("interpretation"):
        interp = d["interpretation"]
        lines += [
            "", "── Interpretation ──",
            f"Theme: {interp['central_theme']}",
            "",
            interp["jungian_analysis"] or "",
            "",
            "── Waking Life ──",
            interp["waking_life"] or "",
            "",
            "── Message ──",
            interp["message"] or "",
        ]

    return "\n".join(lines)


@mcp.tool()
async def list_archetypes() -> str:
    """
    List all Jungian archetypes identified across all dreams,
    with how many times each appeared. Useful for spotting recurring patterns.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{API_BASE}/dreams/symbols", headers=_headers())
        resp.raise_for_status()
        archetypes = resp.json()

    if not archetypes:
        return "No archetypes identified yet."

    lines = ["Archetypes across all dreams:\n"]
    for a in archetypes:
        lines.append(f"  • {a['archetype']} — appeared {a['count']} time(s)")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")
