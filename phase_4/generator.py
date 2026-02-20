"""
Phase 4: Response Generator (Orchestrator)

Connects Phase 3 output → Phase 4 prompt building → Gemini LLM call.

Usage:
    from phase_4.generator import ResponseGenerator

    generator = ResponseGenerator()
    answer = generator.answer(pipeline_output)
    print(answer.text)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from phase_4.prompt_builder import PromptBuilder, BuiltPrompt
from phase_4.llm_client import GroqClient, LLMResponse

logger = logging.getLogger(__name__)


# ── Output data class ─────────────────────────────────────────────────────

@dataclass
class GeneratorResponse:
    """
    The complete output of one Phase 4 cycle.

    Attributes:
        query:          Original user query.
        answer:         LLM-generated answer text (empty on failure).
        llm_response:   Raw LLMResponse for inspection / logging.
        prompt:         The BuiltPrompt sent to the LLM.
        success:        True when we have a real answer.
        error:          Non-None when generation failed.
    """
    query: str
    answer: str
    llm_response: Optional[LLMResponse] = None
    prompt: Optional[BuiltPrompt] = None
    success: bool = False
    error: Optional[str] = None


# ── Response Generator ─────────────────────────────────────────────────────

class ResponseGenerator:
    """
    Orchestrates PromptBuilder → GeminiClient → GeneratorResponse.

    Args:
        llm_client:     A GroqClient instance (or any compatible mock).
        prompt_builder: A PromptBuilder instance with the desired system prompt.
    """

    def __init__(
        self,
        llm_client: Optional[GroqClient] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ):
        self.llm_client = llm_client or GroqClient()
        self.prompt_builder = prompt_builder or PromptBuilder()

    # ── Main entry point ──────────────────────────────────────────────────

    def answer(
        self,
        query: str,
        context_blocks: Optional[List[str]] = None,
    ) -> GeneratorResponse:
        """
        Generate a Gemini answer for the given query + context.

        Args:
            query:          The cleaned (preprocessed) user query from Phase 3.
            context_blocks: List of retrieved text chunks (may be empty).

        Returns:
            A GeneratorResponse with the LLM answer (or error info).
        """
        # Validate query
        if not query or not query.strip():
            return GeneratorResponse(
                query=query or "",
                answer="",
                success=False,
                error="Cannot generate a response for an empty query.",
            )

        # 1 — Build prompt
        try:
            prompt = self.prompt_builder.build(
                query=query,
                context_blocks=context_blocks or [],
            )
        except Exception as exc:
            logger.error(f"PromptBuilder failed: {exc}")
            return GeneratorResponse(
                query=query,
                answer="",
                success=False,
                error=f"Prompt construction error: {exc}",
            )

        # 2 — Call LLM
        llm_response = self.llm_client.generate(
            system_prompt=prompt.system_prompt,
            user_message=prompt.user_message,
        )

        if not llm_response.success:
            logger.error(f"LLM call failed: {llm_response.error}")
            return GeneratorResponse(
                query=query,
                answer="",
                llm_response=llm_response,
                prompt=prompt,
                success=False,
                error=llm_response.error,
            )

        # 3 — Return result
        logger.info(
            f"Generated response for query '{query[:50]}' "
            f"in {llm_response.attempts} attempt(s)."
        )
        return GeneratorResponse(
            query=query,
            answer=llm_response.text,
            llm_response=llm_response,
            prompt=prompt,
            success=True,
        )

    def answer_from_pipeline(self, pipeline_output) -> GeneratorResponse:
        """
        Convenience method: accept a Phase 3 PipelineOutput directly.

        Args:
            pipeline_output: A phase_3.pipeline.PipelineOutput instance.

        Returns:
            A GeneratorResponse.
        """
        # If Phase 3 failed, forward the error without calling the LLM
        if not pipeline_output.success:
            return GeneratorResponse(
                query=pipeline_output.original_query,
                answer="",
                success=False,
                error=(
                    f"Phase 3 error: {pipeline_output.error}"
                    if pipeline_output.error
                    else "No relevant context found."
                ),
            )

        # Split the context string back into blocks for numbered formatting
        context_blocks = [
            block.strip()
            for block in pipeline_output.context_string.split("\n\n---\n\n")
            if block.strip()
        ] if pipeline_output.context_string else []

        return self.answer(
            query=pipeline_output.cleaned_query or pipeline_output.original_query,
            context_blocks=context_blocks,
        )
