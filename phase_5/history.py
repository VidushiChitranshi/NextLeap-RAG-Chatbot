"""
Phase 5: Conversation History Manager

Maintains a rolling window of (user query → chatbot answer) turns
for multi-turn conversation context.

The history is intentionally kept simple and in-memory for Phase 5.
Future phases can swap this for a database-backed store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Turn:
    """A single conversation exchange."""
    query: str
    answer: str
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    is_fallback: bool = False


class ConversationHistory:
    """
    Rolling in-memory store for conversation turns.

    Args:
        max_turns: Maximum number of turns to retain.
                   Older turns are dropped when the limit is exceeded.
    """

    def __init__(self, max_turns: int = 20):
        if max_turns < 1:
            raise ValueError("max_turns must be at least 1.")
        self.max_turns = max_turns
        self._turns: List[Turn] = []

    # ── Public API ────────────────────────────────────────────────────────

    def add(self, query: str, answer: str, is_fallback: bool = False) -> Turn:
        """
        Record a new conversation turn.

        Args:
            query:       The user's question.
            answer:      The chatbot's formatted answer.
            is_fallback: True if the answer was a "no-information" fallback.

        Returns:
            The newly created Turn.
        """
        turn = Turn(query=query, answer=answer, is_fallback=is_fallback)
        self._turns.append(turn)

        # Trim to window
        if len(self._turns) > self.max_turns:
            self._turns = self._turns[-self.max_turns:]

        return turn

    def get_recent(self, n: int) -> List[Turn]:
        """Return the last *n* turns (oldest first)."""
        return self._turns[-n:] if n > 0 else []

    def clear(self) -> None:
        """Erase all conversation history."""
        self._turns = []

    def to_prompt_context(self, n: int = 3) -> str:
        """
        Format the last *n* turns as a context snippet for the LLM.

        Returns an empty string when there is no history.
        """
        turns = self.get_recent(n)
        if not turns:
            return ""
        lines = []
        for t in turns:
            lines.append(f"User: {t.query}")
            lines.append(f"Assistant: {t.answer}")
        return "\n".join(lines)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    @property
    def is_empty(self) -> bool:
        return self.turn_count == 0

    @property
    def last_turn(self) -> Optional[Turn]:
        return self._turns[-1] if self._turns else None
