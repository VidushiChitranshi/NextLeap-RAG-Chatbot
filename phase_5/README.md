# Phase 5: Response Generation Pipeline

## Overview

Phase 5 is the **final layer** of the NextLeap RAG chatbot. It wires the retrieval (Phase 3) and LLM generation (Phase 4) modules together and adds response formatting, citation handling, and multi-turn conversation memory.

```
User Message
      │
      ▼
┌──────────────┐   Phase 3   ┌─────────────────────┐
│   Chatbot    │ ──────────▶ │  RetrievalPipeline   │ Vector search
│ (Orchestrator)│ ◀────────── └─────────────────────┘
│              │   Phase 4   ┌─────────────────────┐
│              │ ──────────▶ │  ResponseGenerator   │ Gemini LLM
│              │ ◀────────── └─────────────────────┘
│              │   Phase 5   ┌─────────────────────┐
│              │ ──────────▶ │  ResponseFormatter   │ Clean + cite
│              │             └─────────────────────┘
│              │   Phase 5   ┌─────────────────────┐
│              │ ──────────▶ │ ConversationHistory  │ Store turn
└──────────────┘             └─────────────────────┘
      │
      ▼
  ChatReply (answer, citations, is_fallback, turn)
```

## Files

| File | Responsibility |
|------|---------------|
| `formatter.py` | Clean LLM output, detect fallback answers, extract citations |
| `history.py` | Rolling in-memory conversation history with LLM context helper |
| `chatbot.py` | `Chatbot` orchestrator — the single public entry point |
| `tests/` | Co-located unit tests (no API calls required) |

## Quick Start

```python
from phase_3.pipeline import RetrievalPipeline
from phase_4.generator import ResponseGenerator
from phase_5.chatbot import Chatbot

# Initialise each phase
pipeline  = RetrievalPipeline(vector_store=store)
generator = ResponseGenerator()               # reads GOOGLE_API_KEY
chatbot   = Chatbot(pipeline, generator)

# Chat
reply = chatbot.chat("What is the fee for the PM fellowship?")
print(reply.answer)
print(reply.citations)   # e.g. ["Pricing", "Overview"]
print(reply.is_fallback) # False if context was found
```

## Run Tests

```bash
# From project root — no API key required
python -m pytest phase_5/tests/ -v
```

## Run All Phases Together

```bash
python -m pytest tests/ phase_3/tests/ phase_4/tests/ phase_5/tests/ -v
```
