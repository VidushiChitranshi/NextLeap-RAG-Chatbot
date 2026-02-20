# Phase 3: Retrieval Module

## Overview

Phase 3 receives a raw user query and returns relevant course-data chunks from the ChromaDB vector store built in Phase 2.

```
Raw User Query
      │
      ▼
┌─────────────────┐
│ QueryPreprocessor│  Clean, validate, injection-guard
└────────┬────────┘
         │ cleaned query
         ▼
┌─────────────────┐
│    Retriever    │  Similarity search (Phase 2 VectorStore)
│                 │  Relevance threshold filter
└────────┬────────┘
         │ List[RetrievalResult]
         ▼
┌─────────────────┐
│   Pipeline      │  Orchestrator — returns PipelineOutput
│   Output        │  → context_string ready for Phase 4 LLM
└─────────────────┘
```

## Files

| File | Responsibility |
|------|---------------|
| `preprocessor.py` | Normalize whitespace, enforce length limits, detect injection patterns |
| `retriever.py` | Similarity search + threshold filtering → `List[RetrievalResult]` |
| `pipeline.py` | Orchestrate preprocess → retrieve → build context string |
| `tests/` | Unit tests for all three modules |

## Key Classes

### `QueryPreprocessor`
```python
from phase_3.preprocessor import QueryPreprocessor

preprocessor = QueryPreprocessor(min_length=3, max_length=500)
cleaned = preprocessor.preprocess("Who are the mentors?")
# → "who are the mentors?"
```

### `Retriever`
```python
from phase_3.retriever import Retriever

retriever = Retriever(vector_store=store, top_k=5, relevance_threshold=0.7)
results = retriever.retrieve("product management pricing")
# → [RetrievalResult(rank=1, score=0.92, content="..."), ...]
```

### `RetrievalPipeline` _(recommended entry point)_
```python
from phase_3.pipeline import RetrievalPipeline

pipeline = RetrievalPipeline(vector_store=store, top_k=5)
output = pipeline.run("What is the course fee?")

if output.success:
    print(output.context_string)  # inject into LLM prompt
else:
    print(output.error)           # forward to user
```

## Running Unit Tests

```bash
# From project root
python -m pytest phase_3/tests/ -v
```

## Dependencies

Phase 3 has **no new package dependencies** beyond what Phase 2 already requires (`langchain-chroma`, `langchain-google-genai`). It imports only from Phase 2 and the Python standard library.
