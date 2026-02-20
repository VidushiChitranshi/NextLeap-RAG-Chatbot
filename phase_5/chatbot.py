"""
Phase 5: Chatbot — End-to-End Orchestrator

The Chatbot class is the single public entry point that wires together:
  Phase 3 → RetrievalPipeline   (vector search)
  Phase 4 → ResponseGenerator   (Gemini LLM)
  Phase 5 → ResponseFormatter   (clean output + citations)
  Phase 5 → ConversationHistory (rolling turn memory)

Usage:
    from phase_5.chatbot import Chatbot

    bot = Chatbot(
        retrieval_pipeline=pipeline,
        response_generator=generator,
    )
    reply = bot.chat("What is the fee for the PM fellowship?")
    print(reply.answer)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from phase_5.formatter import ResponseFormatter, FormattedResponse
from phase_5.history import ConversationHistory, Turn

logger = logging.getLogger(__name__)


# ── Chat reply data class ─────────────────────────────────────────────────

@dataclass
class ChatReply:
    """
    The complete output of one chatbot turn.

    Attributes:
        query:       The original user message.
        answer:      Final, formatted answer text.
        citations:   Source section labels for the answer.
        is_fallback: True when the chatbot had no relevant information.
        success:     False only on hard errors (LLM failure, retrieval crash).
        error:       Non-None description when success is False.
        turn:        The Turn stored in conversation history (None on error).
    """
    query: str
    answer: str
    citations: List[str] = field(default_factory=list)
    is_fallback: bool = False
    success: bool = True
    error: Optional[str] = None
    turn: Optional[Turn] = None


# ── Chatbot ───────────────────────────────────────────────────────────────

class Chatbot:
    """
    Full RAG chatbot combining retrieval, generation, formatting, and history.

    Args:
        retrieval_pipeline:  Phase 3 RetrievalPipeline instance.
        response_generator:  Phase 4 ResponseGenerator instance.
        formatter:           Phase 5 ResponseFormatter (created if omitted).
        history:             Phase 5 ConversationHistory (created if omitted).
        max_history_turns:   Rolling window size when creating history internally.
    """

    def __init__(
        self,
        retrieval_pipeline,
        response_generator,
        formatter: Optional[ResponseFormatter] = None,
        history: Optional[ConversationHistory] = None,
        max_history_turns: int = 20,
    ):
        self.retrieval_pipeline = retrieval_pipeline
        self.response_generator = response_generator
        self.formatter = formatter or ResponseFormatter()
        self.history = history or ConversationHistory(max_turns=max_history_turns)

    # ── Main entry point ──────────────────────────────────────────────────

    def chat(self, user_query: str) -> ChatReply:
        """
        Process one user message through the full RAG pipeline.

        Steps:
          1. Retrieve relevant context (Phase 3).
          2. Generate answer from Gemini (Phase 4).
          3. Format and enrich with citations (Phase 5).
          4. Store in conversation history.

        Args:
            user_query: Raw message from the user interface.

        Returns:
            A ChatReply ready for display.
        """
        if not user_query or not user_query.strip():
            return ChatReply(
                query=user_query or "",
                answer="",
                success=False,
                error="Please enter a question.",
            )

        logger.info(f"Processing user query: '{user_query[:80]}'")

        # ── Step 1: Retrieve ──────────────────────────────────────────────
        retrieval_output = self.retrieval_pipeline.run(user_query)

        if not retrieval_output.success:
            # Retrieval failure still generates a graceful fallback answer
            logger.warning(f"Retrieval failed: {retrieval_output.error}")

        # ── Step 2: Generate ──────────────────────────────────────────────
        gen_response = self.response_generator.answer_from_pipeline(retrieval_output)

        if not gen_response.success and not gen_response.answer:
            return ChatReply(
                query=user_query,
                answer="",
                success=False,
                error=gen_response.error or "Failed to generate a response.",
            )

        # ── Step 3: Format ────────────────────────────────────────────────
        # Collect metadata from retrieval results for citation building
        metadata_list = [r.metadata for r in retrieval_output.results]

        raw_answer = gen_response.answer or ""
        formatted: FormattedResponse = self.formatter.format(
            raw_answer=raw_answer,
            metadata_list=metadata_list,
        )

        # ── Step 4: Store history ─────────────────────────────────────────
        turn = self.history.add(
            query=user_query,
            answer=formatted.answer,
            is_fallback=formatted.is_fallback,
        )

        logger.info(
            f"Chat turn complete. fallback={formatted.is_fallback}, "
            f"citations={formatted.citations}"
        )

        return ChatReply(
            query=user_query,
            answer=formatted.answer,
            citations=formatted.citations,
            is_fallback=formatted.is_fallback,
            success=True,
            turn=turn,
        )

    # ── Convenience accessors ─────────────────────────────────────────────

    def get_history(self, n: int = 10) -> List[Turn]:
        """Return the last *n* conversation turns."""
        return self.history.get_recent(n)

    def clear_history(self) -> None:
        """Wipe the conversation history."""
        self.history.clear()
        logger.info("Conversation history cleared.")

    @property
    def turn_count(self) -> int:
        return self.history.turn_count
