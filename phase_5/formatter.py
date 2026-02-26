"""
Phase 5: Response Formatter

Transforms the raw LLM answer into a polished, user-facing response.

Responsibilities:
  - Strip extraneous whitespace / artefacts from LLM output.
  - Append a source citation line when context metadata is available.
  - Detect and label "no-information" fallback responses.
  - Optionally wrap the answer in a structured FormattedResponse object
    that downstream interfaces (CLI, API, web) can easily consume.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Sentinel phrases the LLM uses when it has no information ──────────────
_NO_INFO_PHRASES = [
    "i'm sorry, i don't have",
    "i don't have specific information",
    "please visit https://nextleap.app",
    "no relevant context was found",
    "i cannot answer",
    "not enough information",
]


@dataclass
class FormattedResponse:
    """
    A polished response ready for the user interface.

    Attributes:
        answer:          Final cleaned answer text.
        citations:       Source labels extracted from chunk metadata.
        is_fallback:     True when the LLM signalled it had no information.
        raw_answer:      The original, unprocessed LLM answer.
        character_count: Length of the formatted answer (for UI hints).
    """
    answer: str
    citations: List[str] = field(default_factory=list)
    is_fallback: bool = False
    raw_answer: str = ""

    @property
    def character_count(self) -> int:
        return len(self.answer)

    @property
    def has_citations(self) -> bool:
        return bool(self.citations)

    def to_dict(self) -> dict:
        """Serialise for JSON / API responses."""
        return {
            "answer": self.answer,
            "citations": self.citations,
            "is_fallback": self.is_fallback,
            "character_count": self.character_count,
        }


class ResponseFormatter:
    """
    Cleans LLM output and enriches it with citation metadata.

    Args:
        include_citations: Whether to append a citations line to the answer.
        citation_prefix:   Label placed before the citations list.
    """

    def __init__(
        self,
        include_citations: bool = True,
        citation_prefix: str = "\n\n📚 **Sources:** ",
    ):
        self.include_citations = include_citations
        self.citation_prefix = citation_prefix

    # ── Public API ────────────────────────────────────────────────────────

    def format(
        self,
        raw_answer: str,
        metadata_list: Optional[List[dict]] = None,
    ) -> FormattedResponse:
        """
        Format a raw LLM answer.

        Args:
            raw_answer:     The text returned by the Gemini client.
            metadata_list:  List of chunk metadata dicts from Phase 3 results.
                            Used to build the citations list.

        Returns:
            A FormattedResponse ready for the user.
        """
        if not raw_answer or not raw_answer.strip():
            return FormattedResponse(
                answer="I'm sorry, I couldn't generate a response. Please try again.",
                is_fallback=True,
                raw_answer=raw_answer or "",
            )

        cleaned = self._clean(raw_answer)
        is_fallback = self._detect_fallback(cleaned)
        citations = self._extract_citations(metadata_list or [])

        # Only append citations when we have real content (not a fallback)
        answer = cleaned
        if self.include_citations and citations and not is_fallback:
            answer = cleaned + self.citation_prefix + ", ".join(citations)

        return FormattedResponse(
            answer=answer,
            citations=citations,
            is_fallback=is_fallback,
            raw_answer=raw_answer,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Normalize whitespace and strip markdown artefacts."""
        # Collapse 3+ consecutive newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace
        return text.strip()

    @staticmethod
    def _detect_fallback(text: str) -> bool:
        """Return True if the answer matches a known no-information pattern."""
        lower = text.lower()
        return any(phrase in lower for phrase in _NO_INFO_PHRASES)

    @staticmethod
    def _extract_citations(metadata_list: List[dict]) -> List[str]:
        """
        Build a de-duplicated, human-readable citations list from chunk metadata.

        - Skips generic labels like 'Pricing', 'Overview', 'Faculty'.
        - Always prioritizes and includes the 'source' URL if available.
        """
        seen: set = set()
        citations: List[str] = []
        
        # Tags to exclude from the UI
        excluded_tags = {"Pricing", "Overview", "Faculty"}

        for meta in metadata_list:
            section = meta.get("section_type", "")
            source = meta.get("source", "")

            # 1. Try to get a section label
            label = section.replace("_", " ").title() if section else ""
            
            # 2. Add source URL if available (this is now requested by the user)
            if source and source not in seen:
                seen.add(source)
                citations.append(source)

            # 3. Add section label only if it's not in the excluded list and not already seen
            if label and label not in excluded_tags and label not in seen:
                seen.add(label)
                citations.append(label)

        return citations
