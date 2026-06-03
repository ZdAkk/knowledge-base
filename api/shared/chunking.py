"""
Paragraph-aware sliding window chunker.
Splits text on blank lines, then builds overlapping windows by word count.
This approach respects natural sentence/paragraph boundaries, which produces
much better retrieval results than fixed character-count splits.
"""

import hashlib
import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str
    approx_tokens: int
    start_paragraph: int
    end_paragraph_exclusive: int
    sha256: str


def clean_text(text: str) -> str:
    """
    Remove noise that hurts retrieval quality:
    - Image markdown: ![alt](path)
    - Decorative separators: ---, * * *, etc.
    - Collapse excessive blank lines
    """
    # Remove image markdown
    text = re.sub(r"^!\[.*?\]\(.*?\)\s*$", "", text, flags=re.MULTILINE)
    # Remove decorative separators
    text = re.sub(r"^[\s\*\-·_=•]{1,10}$", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_paragraphs(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p.strip() for p in re.split(r"\n\s*\n+", normalized) if p.strip()]


def approx_word_count(text: str) -> int:
    return len(text.split())


def split_oversized_paragraph(text: str, max_words: int) -> list[str]:
    """
    Hard-split a paragraph that exceeds max_words into word-count chunks.
    Used as a safety net for unusually long paragraphs (e.g. poetry, legal text).
    """
    words = text.split()
    parts = []
    for i in range(0, len(words), max_words):
        parts.append(" ".join(words[i:i + max_words]))
    return parts


def chunk_text(
    text: str,
    max_tokens: int = 450,
    overlap_tokens: int = 80,
    # OpenAI text-embedding-3-large limit is 8192 tokens (~6000 words).
    # Hard-split any paragraph exceeding this to prevent API errors.
    hard_max_words: int = 5000,
) -> list[Chunk]:
    """
    Split text into overlapping chunks by paragraph windows.
    max_tokens and overlap_tokens are approximated as word counts.
    Paragraphs exceeding hard_max_words are forcibly split first.
    """
    cleaned = clean_text(text)
    raw_paragraphs = split_paragraphs(cleaned)

    # Enforce hard limit on individual paragraphs
    paragraphs = []
    for p in raw_paragraphs:
        if approx_word_count(p) > hard_max_words:
            paragraphs.extend(split_oversized_paragraph(p, hard_max_words))
        else:
            paragraphs.append(p)

    if not paragraphs:
        return []


    chunks: list[Chunk] = []
    chunk_index = 0
    start = 0

    while start < len(paragraphs):
        end = start
        combined = ""

        while end < len(paragraphs):
            candidate = f"{combined}\n\n{paragraphs[end]}" if combined else paragraphs[end]
            word_count = approx_word_count(candidate)
            if word_count > max_tokens and end > start:
                break
            combined = candidate
            end += 1
            if approx_word_count(combined) >= max_tokens:
                break

        text_out = combined.strip()
        if text_out:
            chunks.append(Chunk(
                index=chunk_index,
                text=text_out,
                approx_tokens=approx_word_count(text_out),
                start_paragraph=start,
                end_paragraph_exclusive=end,
                sha256=hashlib.sha256(text_out.encode()).hexdigest(),
            ))
            chunk_index += 1

        if end >= len(paragraphs):
            break

        # Slide back to create overlap
        if overlap_tokens > 0:
            overlap_start = end
            accum = 0
            while overlap_start > start:
                overlap_start -= 1
                accum += approx_word_count(paragraphs[overlap_start])
                if accum >= overlap_tokens:
                    break
            start = max(overlap_start, start + 1)
        else:
            start = end

    return chunks
