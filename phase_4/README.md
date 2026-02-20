# Phase 4: LLM Integration Module

## Overview

Phase 4 receives retrieved context from Phase 3 and generates a natural-language answer using **Google Gemini 1.5 Flash** (or Pro).

```
Phase 3 PipelineOutput
        │
        ▼
┌──────────────────┐
│  PromptBuilder   │  System prompt + numbered context blocks + user query
└────────┬─────────┘
         │ BuiltPrompt
         ▼
┌──────────────────┐
│  GeminiClient    │  API call with exponential-backoff retry
└────────┬─────────┘
         │ LLMResponse
         ▼
┌──────────────────┐
│ ResponseGenerator│  Orchestrator → GeneratorResponse
└──────────────────┘
```

## Files

| File | Responsibility |
|------|---------------|
| `prompt_builder.py` | Build system prompt + inject numbered context + user query |
| `llm_client.py` | Gemini SDK wrapper with retry and `LLMResponse` dataclass |
| `generator.py` | Orchestrator — accepts Phase 3 output, returns `GeneratorResponse` |
| `tests/` | Co-located unit tests (no real API calls) |

## Quick Start

```python
from phase_4.generator import ResponseGenerator

# Inject a mock or real GeminiClient
generator = ResponseGenerator()

# Option A: pass query + context blocks directly
response = generator.answer(
    query="what is the course fee?",
    context_blocks=["Pricing: INR 36,999 (Cohort 47, OPEN)"],
)
print(response.answer)

# Option B: pass Phase 3 PipelineOutput
from phase_3.pipeline import RetrievalPipeline
pipeline = RetrievalPipeline(vector_store=store)
output = pipeline.run("What is the course fee?")

response = generator.answer_from_pipeline(output)
print(response.answer)
```

## Environment Variable Required

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Running Unit Tests

```bash
# From project root — no API key required
python -m pytest phase_4/tests/ -v
```

## Dependencies

```
google-generativeai>=0.5.0
```

Add to `requirements.txt` if not already present.
