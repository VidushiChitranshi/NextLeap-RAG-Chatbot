"""
Phase 3: Retrieval Pipeline (Orchestrator)

Combines the QueryPreprocessor and Retriever into a single high-level
entry point used by downstream phases (Phase 4 LLM Integration).

Usage:
    from phase_3.pipeline import RetrievalPipeline

    pipeline = RetrievalPipeline(vector_store=store)
    context  = pipeline.run("Who are the mentors?")
    # context.results  → list[RetrievalResult]
    # context.context_string → formatted text for LLM prompt
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from phase_3.preprocessor import QueryPreprocessor
from phase_3.retriever import Retriever, RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineOutput:
    """
    The complete output of one retrieval pipeline run.

    Attributes:
        original_query:  The raw string entered by the user.
        cleaned_query:   The preprocessed version used for embedding.
        results:         Ranked list of RetrievalResult objects.
        context_string:  Results joined into a single LLM-ready string.
        error:           Non-None when the pipeline encountered a handled error
                         (e.g. invalid query, no results).
    """
    original_query: str
    cleaned_query: str = ""
    results: List[RetrievalResult] = field(default_factory=list)
    context_string: str = ""
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """True when the pipeline returned at least one result without error."""
        return self.error is None and len(self.results) > 0


class RetrievalPipeline:
    """
    End-to-end retrieval pipeline for Phase 3.

    Orchestrates:
      1. QueryPreprocessor  — clean and validate the raw user query
      2. Retriever          — search the vector store, apply threshold filter
      3. PipelineOutput     — bundle results + context string

    Args:
        vector_store:        Initialised phase_2.store.VectorStore instance.
        top_k:               Number of chunks to retrieve.
        relevance_threshold: Minimum similarity score (or None to disable).
        context_separator:   Separator used when joining context blocks.
        min_query_length:    Minimum cleaned-query length (chars).
        max_query_length:    Maximum cleaned-query length (chars).
    """

    def __init__(
        self,
        vector_store,
        top_k: int = 5,
        relevance_threshold: Optional[float] = None,
        context_separator: str = "\n\n---\n\n",
        min_query_length: int = 3,
        max_query_length: int = 500,
    ):
        self.preprocessor = QueryPreprocessor(
            min_length=min_query_length,
            max_length=max_query_length,
        )
        self.retriever = Retriever(
            vector_store=vector_store,
            top_k=top_k,
            relevance_threshold=relevance_threshold,
        )
        self.context_separator = context_separator

    def run(self, raw_query: str) -> PipelineOutput:
        """
        Execute the full retrieval pipeline for a single user query.

        Args:
            raw_query: Raw string from the user interface.

        Returns:
            A PipelineOutput containing results (and any error description).
        """
        output = PipelineOutput(original_query=raw_query)

        # Step 1 — Preprocess
        try:
            cleaned = self.preprocessor.preprocess(raw_query)
            output.cleaned_query = cleaned
        except ValueError as e:
            output.error = str(e)
            logger.warning(f"Query rejected by preprocessor: {e}")
            return output

        # Step 2 — Retrieve
        results = self.retriever.retrieve(cleaned)
        output.results = results

        # Step 3 — Build context string
        if results:
            output.context_string = self.context_separator.join(
                r.content for r in results
            )
        else:
            output.error = (
                "No relevant information found for your query. "
                "Please try rephrasing or ask something about the NextLeap course."
            )
            logger.info("Pipeline produced zero results — setting error message.")

        return output
