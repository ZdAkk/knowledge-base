# Dream Log Automation — Trigger.dev Implementation Brief

## Context

This automation lives in the `personal-automations` repository alongside existing automations (`deep-dive.ts`, `weekly-review.ts`, `peer-review.ts`). Follow the exact same patterns — parent/child task structure, poller using `schedules.task`, sequential `triggerAndWait` calls, idempotency keys, tag-based double-processing prevention. Read the existing files thoroughly before writing anything.

The target is a self-hosted knowledge base API at `https://knowledgebase-api.alakad.de` that stores dream records, interprets them using Jungian psychology, and makes them searchable via pgvector embeddings.

---

## New File to Create

**`src/trigger/dream-log.ts`** — the entire automation lives here.

---

## New Library File to Create

**`src/lib/knowledge-base.ts`** — API client for the knowledge base. Mirror the style and structure of `src/lib/clickup.ts` exactly. Should expose:

```typescript
searchBooks(query: string, limit?: number, threshold?: number): Promise<BookSearchResult[]>
ingestDream(payload: DreamIngestPayload): Promise<{ dream_id: string }>
addInterpretation(dreamId: string, payload: InterpretationPayload): Promise<void>
```

All requests must include `Authorization: Bearer ${KNOWLEDGE_BASE_API_KEY}` header. Base URL from `KNOWLEDGE_BASE_BASE_URL` env var.

### API Contract

`POST /dreams/ingest` — body:
```json
{
  "dreamed_on": "2026-05-29",
  "raw_text": "...",
  "cleaned_text": "...",
  "title": "...",
  "emotional_tone": ["fear", "accomplishment"],
  "lucid": false,
  "recurring": false,
  "notes": null,
  "day_residue": "brief summary of what the dreamer experienced the day before"
}
```
Returns `{ "dream_id": "uuid" }`

`POST /dreams/{dream_id}/interpretation` — body:
```json
{
  "central_theme": "...",
  "jungian_analysis": "...",
  "waking_life": "...",
  "message": "...",
  "symbols": [
    {
      "name": "The Heavyset Man",
      "archetype": "The Shadow",
      "description": "...",
      "significance": "...",
      "jungian_concept": "Shadow"
    }
  ],
  "books_used": ["man-and-his-symbols"],
  "web_sources": ["https://..."],
  "scholar_sources": null,
  "model_used": "deepseek/deepseek-r1"
}
```

`GET /books/search?q=...&limit=5&threshold=0.3` — returns `{ results: [{ title, chapter_title, text, similarity }] }`

---

## Environment Variables

Add to `.env` and `.env.example`:

```env
# Knowledge Base API
KNOWLEDGE_BASE_BASE_URL=https://knowledgebase-api.alakad.de
KNOWLEDGE_BASE_API_KEY=

# ClickUp — Dream Log list (separate from existing CLICKUP_LIST_ID)
CLICKUP_DREAM_LIST_ID=

# Models via OpenRouter
DREAM_CLEANER_MODEL=deepseek/deepseek-r1
DREAM_RESEARCHER_MODEL=perplexity/sonar-pro
DREAM_SYNTHESIZER_MODEL=deepseek/deepseek-r1
```

---

## ClickUp List Setup

Create a ClickUp list called **"Dream Log"** with these statuses:
- `Raw` — you drop the dream in here
- `Processing` — automation moves it here on start
- `Done` — automation moves it here on success
- `Error` — automation moves it here on failure

**User experience:** Drop a task into the list with the raw dream text in the task description. That is all. The task name is ignored. The date is derived automatically from the task's `date_created` field: `new Date(parseInt(task.date_created)).toISOString().split("T")[0]`. No other fields need to be filled in manually.

---

## Automation Flow

Follow the deep-dive pattern exactly.

```
dreamLogPoller (schedules.task, every 2 min)
  → finds tasks in "Raw" status in CLICKUP_DREAM_LIST_ID without "dream-processing-started" tag
  → tags task immediately (prevent double-processing)
  → moves status to "Processing"
  → triggers dreamLog parent with idempotencyKey: `dream-log-${taskId}`

dreamLog (parent task)
  → triggerAndWait: dreamCleaner         → returns { dream_id, key_themes, symbols, cleaned_text, day_residue }
  → triggerAndWait: knowledgeBaseSearcher → returns { kb_context, books_used }
  → triggerAndWait: scholarlyResearcher  → returns { scholarly_context, web_sources }
  → triggerAndWait: dreamSynthesizer     → returns { interpretation }
  → posts summary comment to ClickUp task
  → moves status to "Done"
  → removes "dream-processing-started" tag
  → on any failure: moves status to "Error", removes tag, posts error comment with details
```

---

## Child Tasks

### `dreamCleaner`

Input: `{ taskId: string, rawText: string, dreamedOn: string }`

- `dreamedOn` derived from ClickUp task `date_created`: `new Date(parseInt(task.date_created)).toISOString().split("T")[0]`
- Calls `DREAM_CLEANER_MODEL` (DeepSeek) via `chat()` from `src/lib/ai.ts`
- Instruct strictly in the prompt to return only valid JSON, no markdown, no explanation
- Returns JSON:
```json
{
  "title": "short evocative title for the dream",
  "cleaned_text": "polished narrative version of the raw dream",
  "emotional_tone": ["fear", "accomplishment"],
  "lucid": false,
  "day_residue": "what the dreamer experienced, encountered, or was preoccupied with in the day or two before the dream — extracted from the raw text if mentioned, otherwise null",
  "key_themes": ["shadow confrontation", "authority figure", "descent"],
  "symbols": ["heavyset man", "slide", "gun"]
}
```
- Calls `POST /dreams/ingest` with the full payload including `raw_text`, `cleaned_text`, `title`, `emotional_tone`, `lucid`, `dreamed_on`, and `day_residue`
- Returns `{ dream_id, key_themes, symbols, cleaned_text, day_residue }`

---

### `knowledgeBaseSearcher`

Input: `{ dream_id: string, key_themes: string[], symbols: string[], cleaned_text: string }`

- Calls `GET /books/search` for each key theme and symbol (up to 4 queries, limit 3 results each)
- Deduplicates results by chunk_id
- Formats results as a readable string: book title, chapter, passage text
- Returns `{ kb_context: string, books_used: string[] }`

---

### `scholarlyResearcher`

Input: `{ key_themes: string[], symbols: string[] }`

- Calls `researchWithBrowsing()` from `src/lib/ai.ts` using `DREAM_RESEARCHER_MODEL` (Perplexity Sonar Pro)
- Query: `"Jungian psychological analysis of [themes and symbols joined] — scholarly sources and archetypes"`
- Returns `{ scholarly_context: string, web_sources: string[] }`

---

### `dreamSynthesizer`

Input: `{ dream_id: string, cleaned_text: string, day_residue: string | null, kb_context: string, scholarly_context: string, symbols: string[] }`

- Calls `DREAM_SYNTHESIZER_MODEL` (DeepSeek) via `chat()` from `src/lib/ai.ts`
- Use the system prompt below (verbatim)
- Parse JSON response defensively — wrap in try/catch and throw a descriptive error if parsing fails
- Calls `POST /dreams/{dream_id}/interpretation` with full payload including `model_used: process.env.DREAM_SYNTHESIZER_MODEL`
- Returns the interpretation object for the parent to use in the ClickUp comment

#### Synthesizer System Prompt

```
You are a depth psychologist in the tradition of Carl Gustav Jung. You have spent sixty years sitting with patients and their dreams. You do not interpret dreams mechanically or impose meanings from outside — you listen to what the psyche is trying to say, on its own terms, in its own language.

Your interpretive framework rests on several principles that you must never abandon:

1. THE DREAM IS NOT A DISGUISE. Unlike Freud, you do not believe the dream hides its meaning. The dream says exactly what it means — but in the language of images, not of rational thought. Your task is translation, not decryption.

2. PERSONAL ASSOCIATION BEFORE AMPLIFICATION. Before reaching for mythology or collective symbolism, you must always ask: what does this image mean to *this* dreamer? A gun is not universally a symbol of aggression. A professor is not universally a Wise Old Man. You must first exhaust the personal dimension — what the dreamer associates with this figure, this object, this place, especially in the days leading up to the dream. Only when the personal layer is fully explored do you widen outward to archetypal parallels.

3. DAY RESIDUE IS NOT NOISE — IT IS THE DOORWAY. The experiences of the previous day are not accidental material that the unconscious happens to pick up. They are the specific entry points the psyche chose. The unconscious selects from waking experience precisely those images that carry the energetic charge it needs to make its statement. If the dreamer encountered an authority figure the day before and that figure appears in the dream, this is not coincidence — it is the unconscious using a ready-made vessel. Always interpret the day residue as a deliberate choice by the psyche, not as background noise.

4. THE DREAM COMPENSATES. The unconscious does not tell the dreamer what the conscious mind already knows. It compensates — it brings forward what is missing, suppressed, undeveloped, or dangerously one-sided in the dreamer's conscious attitude. Ask yourself: what is the dreamer's conscious position, and how does this dream correct, deepen, or challenge it?

5. SYMBOLS ARE ALIVE, NOT FIXED. A symbol from the collective unconscious — the Shadow, the Anima, the Wise Old Man, the descent — is a living psychic reality, not a label to be applied. When you name an archetype, you must show how it is alive and specific in *this* dream, *this* dreamer's life. The archetypal name is the beginning of the interpretation, not the end.

6. THE SELF SPEAKS IN WHOLE SITUATIONS, NOT SINGLE IMAGES. Read the dream as a drama — with a setting, a development, a climax, a resolution or lack thereof. The narrative structure itself carries meaning. A dream that ends in escape means something different from one that ends in victory, surrender, or ambiguity.

7. DO NOT MORALIZE. You do not tell the dreamer what they should do. You tell them what the unconscious is already doing — what it is working on, what it is trying to integrate. The psyche knows its direction. Your job is to make it visible.

You will receive:
- The dreamer's cleaned dream narrative
- Day residue: what the dreamer experienced in the day or two before the dream. Use this as your primary personal context — it tells you which symbols are personally charged, not just archetypally relevant. If day residue is null, note its absence but proceed with the archetypal layer.
- Relevant passages from a library of Jungian and depth psychology texts — use these for amplification after personal associations are explored
- Scholarly research on the specific symbols and themes present

Produce your interpretation as a JSON object with these fields:
- central_theme: one sentence naming the core psychological drama of this dream
- jungian_analysis: your full interpretation — structured as a drama (setting → development → climax → resolution), addressing each major symbol in order of appearance, grounding each first in the day residue and personal context before widening to archetypal meaning, referencing the library passages where relevant
- waking_life: how this dream speaks to the dreamer's current life situation — what the unconscious is compensating for, what it is trying to bring forward
- message: the psyche's core statement in 2-3 sentences — not advice, but what the unconscious is doing
- symbols: array of objects: { name, archetype, description, significance, jungian_concept }
- books_used: array of book slugs referenced
- web_sources: array of URLs cited

Return only valid JSON. No markdown. No preamble. No explanation outside the JSON.
```

---

### ClickUp Comment Format

Posted by the parent task on success:

```
## 🌙 Dream Interpretation Complete

**Theme:** {central_theme}

**Message:** {message}

---
*Full analysis stored in knowledge base — dream_id: {dream_id}*
*Interpreted using Jungian analytical psychology · {model}*
```

---

## Key Patterns (mandatory — from existing codebase)

- Use `logger.log()` at the start and end of every child task
- Always check `if (!result.ok) throw new Error(result.error)` after every `triggerAndWait`
- Use `idempotencyKey` on the parent trigger
- Tag the ClickUp task *before* triggering the parent — prevents race conditions if poller fires again before parent starts
- Wrap entire parent body in try/catch — on error: move to `Error` status, remove the processing tag, post a comment with the error message
- Read `CLICKUP_DREAM_LIST_ID` from env, throw clearly if not set
- `triggerAndWait` calls must be sequential — do not wrap in `Promise.all`
- Parse all JSON responses from AI calls defensively — wrap in try/catch and throw a descriptive error if parsing fails so the parent can catch it and move the task to `Error`
