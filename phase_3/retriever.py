"""
Phase 3: Retriever

Encapsulates the vector-search pipeline:
  1. Accept a cleaned query string
  2. Run similarity search against the ChromaDB vector store (from phase_2)
  3. Apply a relevance-score threshold to filter low-quality results
  4. Return ranked RetrievalResult objects ready for the LLM prompt

The Retriever deliberately depends only on the phase_2.store.VectorStore
interface — it never touches ChromaDB or embedding models directly.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """
    A single piece of retrieved context.

    Attributes:
        content:    The text chunk surfaced by the vector search.
        score:      Cosine-similarity score in [0, 1] (higher = more relevant).
                    None when the underlying store doesn't return scores.
        metadata:   Metadata attached to the chunk (source, section_type, …).
        rank:       1-based position among results returned for this query.
    """
    content: str
    score: Optional[float]
    metadata: dict = field(default_factory=dict)
    rank: int = 0

    def __repr__(self) -> str:
        score_str = f"{self.score:.3f}" if self.score is not None else "N/A"
        return (
            f"RetrievalResult(rank={self.rank}, score={score_str}, "
            f"content={self.content[:60]!r})"
        )


class Retriever:
    """
    Retrieves relevant document chunks from the vector store for a given query.

    Args:
        vector_store:        An initialised phase_2.store.VectorStore instance.
        top_k:               Maximum number of results to request from the store.
        relevance_threshold: Minimum similarity score to accept a result.
                             Pass ``None`` to disable threshold filtering
                             (e.g. when scores are unavailable).
    """

    def __init__(
        self,
        vector_store,
        top_k: int = 5,
        relevance_threshold: Optional[float] = None,
    ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold

    def retrieve(self, query: str) -> List[RetrievalResult]:
        """
        Search the vector store for chunks relevant to *query*.

        Args:
            query: A cleaned (pre-processed) query string.

        Returns:
            A list of RetrievalResult objects, ordered by relevance (best first).
            Returns an empty list if no results pass the threshold.
        """
        if not query or not query.strip():
            logger.warning("Retriever received an empty query — returning [].")
            return []

        logger.info(f"Retrieving top-{self.top_k} results for query: '{query}'")

        try:
            # Try the scored variant first (returns (Document, score) tuples)
            if hasattr(self.vector_store, "similarity_search_with_score"):
                raw = self.vector_store.similarity_search_with_score(
                    query, k=self.top_k
                )
                documents_with_scores = [
                    (doc, float(score)) for doc, score in raw
                ]
            else:
                # Fallback to unscored search
                docs = self.vector_store.query_similar(query, k=self.top_k)
                documents_with_scores = [(doc, None) for doc in docs]

        except Exception as e:
            logger.error(f"Vector store search failed: {e}")
            return []

        results: List[RetrievalResult] = []
        for rank, (doc, score) in enumerate(documents_with_scores, start=1):
            # Apply threshold filter (only when score is available)
            if (
                score is not None
                and self.relevance_threshold is not None
                and score < self.relevance_threshold
            ):
                logger.debug(
                    f"Result {rank} dropped (score {score:.3f} < "
                    f"threshold {self.relevance_threshold})"
                )
                continue

            results.append(
                RetrievalResult(
                    content=doc.page_content,
                    score=score,
                    metadata=doc.metadata,
                    rank=rank,
                )
            )

        logger.info(f"Returning {len(results)} result(s) after threshold filter.")
        return results

    def get_context_string(self, query: str, separator: str = "\n\n---\n\n") -> str:
        """
        Convenience method: retrieve results and join their content into a
        single formatted string suitable for injection into an LLM prompt.

        Args:
            query:     A cleaned query string.
            separator: String used to delimit context blocks.

        Returns:
            A formatted string of retrieved context, or an empty string
            if no relevant results were found.
        """
        results = self.retrieve(query)
        if not results:
            return ""
        return separator.join(r.content for r in results)
