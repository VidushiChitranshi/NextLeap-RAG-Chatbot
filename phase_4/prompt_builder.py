"""
Phase 4: Prompt Builder

Constructs the structured prompt sent to the Gemini LLM.

Two parts:
  1. System prompt  — defines the chatbot persona and hard constraints.
  2. User message   — injects retrieved context + raw user query.

Design choices:
  - Keeps system and user messages separate so callers can use them
    with multi-turn chat APIs (e.g. send system once, stream user turns).
  - Context blocks are numbered for easy citation by the LLM.
  - Falls back gracefully when no context is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# ── Default system prompt ─────────────────────────────────────────────────

_DEFAULT_SYSTEM_PROMPT = """\
You are a helpful and professional admissions assistant for NextLeap, \
an ed-tech platform offering fellowship programmes in Product Management, \
Business Analytics, Data Analytics, and UI/UX Design.

Guidelines:
1. Answer ONLY using the information provided in the CONTEXT BLOCKS below.
2. If the context does not contain the answer, respond with:
   "I'm sorry, I don't have specific information on that. \
Please visit https://nextleap.app or contact the admissions team directly."
3. Be concise, friendly, and precise.
4. When citing information, reference the source section, e.g.:
   "According to the pricing section, ..."
5. Never fabricate course details, dates, prices, or instructor names.
"""


# ── Data classes ──────────────────────────────────────────────────────────

@dataclass
class BuiltPrompt:
    """
    The complete, structured prompt ready to send to the LLM.

    Attributes:
        system_prompt:  Instructions that define the model's persona.
        user_message:   Context blocks + user query, formatted for sending.
        has_context:    True when at least one context block was injected.
    """
    system_prompt: str
    user_message: str
    has_context: bool

    def as_single_string(self, separator: str = "\n\n") -> str:
        """Merge system_prompt + user_message into one string (for simple APIs)."""
        return separator.join([self.system_prompt, self.user_message])


# ── Prompt Builder ────────────────────────────────────────────────────────

class PromptBuilder:
    """
    Builds a structured prompt for the NextLeap admissions chatbot.

    Args:
        system_prompt:    Override the default system prompt (optional).
        max_context_chars: Truncate the context string if it exceeds this
                          many characters (prevents token overflow).
                          Set to None to disable truncation.
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        max_context_chars: Optional[int] = 4000,
    ):
        self.system_prompt = system_prompt or _DEFAULT_SYSTEM_PROMPT
        self.max_context_chars = max_context_chars

    # ── Public API ────────────────────────────────────────────────────────

    def build(
        self,
        query: str,
        context_blocks: Optional[List[str]] = None,
    ) -> BuiltPrompt:
        """
        Assemble the full prompt.

        Args:
            query:          The cleaned user query from Phase 3.
            context_blocks: List of text chunks retrieved by Phase 3.
                            Pass an empty list or None when no context found.

        Returns:
            A BuiltPrompt with system_prompt and user_message fields.
        """
        if not query or not query.strip():
            raise ValueError("Query must be a non-empty string.")

        context_blocks = context_blocks or []
        has_context = bool(context_blocks)

        context_section = self._format_context(context_blocks)
        user_message = self._format_user_message(query, context_section, has_context)

        return BuiltPrompt(
            system_prompt=self.system_prompt,
            user_message=user_message,
            has_context=has_context,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _format_context(self, blocks: List[str]) -> str:
        """Serialize context blocks into numbered sections."""
        if not blocks:
            return ""

        context_str = "\n\n".join(
            f"[Block {i+1}]\n{block.strip()}" for i, block in enumerate(blocks)
        )

        # Truncate if needed
        if self.max_context_chars and len(context_str) > self.max_context_chars:
            context_str = context_str[: self.max_context_chars] + "\n... [truncated]"

        return context_str

    def _format_user_message(
        self, query: str, context_section: str, has_context: bool
    ) -> str:
        """Compose the full user-turn message."""
        if has_context:
            return (
                "CONTEXT BLOCKS (retrieved from the NextLeap knowledge base):\n"
                f"{context_section}\n\n"
                f"USER QUESTION: {query.strip()}"
            )
        return (
            "No relevant context was found in the knowledge base.\n\n"
            f"USER QUESTION: {query.strip()}"
        )
