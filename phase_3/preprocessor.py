"""
Phase 3: Query Preprocessor

Cleans and validates user queries before embedding them for retrieval.
Handles:
  - Whitespace normalization
  - Lowercase conversion
  - Minimum-length guard
  - Basic injection-pattern detection
"""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that may indicate prompt-injection or off-topic abuse
_INJECTION_PATTERNS = [
    r"ignore\b.{0,30}\binstructions?",
    r"you are now",
    r"act as",
    r"disregard (the |your )?(above|system|previous)",
    r"<\s*script",
    r"--|;|drop table",
]
_COMPILED_INJECTIONS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


class QueryPreprocessor:
    """
    Preprocesses a raw user query into a clean, safe string ready for embedding.
    """

    def __init__(self, min_length: int = 3, max_length: int = 500):
        self.min_length = min_length
        self.max_length = max_length

    def preprocess(self, raw_query: str) -> str:
        """
        Clean and validate a user query.

        Args:
            raw_query: The raw string from the user interface.

        Returns:
            A cleaned, lowercase, whitespace-normalised query string.

        Raises:
            ValueError: If the query is empty, too short, too long,
                        or triggers an injection guard.
        """
        if not isinstance(raw_query, str):
            raise ValueError("Query must be a string.")

        # Strip surrounding whitespace
        query = raw_query.strip()

        if not query:
            raise ValueError("Query must not be empty.")

        # Collapse multiple internal whitespace characters into one space
        query = re.sub(r"\s+", " ", query)

        # Length guards
        if len(query) < self.min_length:
            raise ValueError(
                f"Query is too short (min {self.min_length} chars): '{query}'"
            )
        if len(query) > self.max_length:
            raise ValueError(
                f"Query is too long (max {self.max_length} chars). "
                f"Got {len(query)} chars."
            )

        # Injection guard
        for pattern in _COMPILED_INJECTIONS:
            if pattern.search(query):
                logger.warning("Potential injection pattern detected in query.")
                raise ValueError(
                    "Query contains disallowed patterns. "
                    "Please ask a relevant question about the NextLeap course."
                )

        # Normalise to lowercase for consistent embedding
        cleaned = query.lower()
        logger.debug(f"Preprocessed query: '{cleaned}'")
        return cleaned
