"""
Phase 4: Groq LLM Client

A thin, testable wrapper around the Groq Python SDK.

Responsibilities:
  - Load and validate GROQ_API_KEY from the environment.
  - Send a built prompt (system + user message) to the Groq model.
  - Return a structured LLMResponse object.
  - Handle transient API errors with retry logic.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Default configuration ─────────────────────────────────────────────────

# Using Llama 3.3 70B via Groq for high performance
DEFAULT_MODEL = "llama-3.3-70b-versatile" 
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0   # seconds between retries

# ── Response data class ───────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """
    Result of one LLM call.

    Attributes:
        text:        The generated answer text (empty string on failure).
        model:       Model name that produced the response.
        success:     True when the API call completed without errors.
        error:       Non-None error description if success is False.
        attempts:    Number of API call attempts made.
    """
    text: str
    model: str
    success: bool
    error: Optional[str] = None
    attempts: int = 1

    def __bool__(self) -> bool:
        return self.success


# ── Groq Client ───────────────────────────────────────────────────────────

class GroqClient:
    """
    Wraps the Groq SDK to call Llama/Mixtral models.

    Args:
        model_name:   Groq model to use (default: llama-3.3-70b-versatile).
        max_retries:  How many times to retry on transient errors.
        retry_delay:  Initial delay (seconds) between retries.
        temperature:  Sampling temperature (0.0–1.0).
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        temperature: float = 0.2,
    ):
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.temperature = temperature
        self._client = None  # Lazy-initialized

    # ── Public API ────────────────────────────────────────────────────────

    def generate(self, system_prompt: str, user_message: str) -> LLMResponse:
        """
        Send a prompt to Groq and return the text response.

        Args:
            system_prompt: The model persona / instructions.
            user_message:  Context blocks + user query.

        Returns:
            LLMResponse with the generated text.
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return LLMResponse(
                text="",
                model=self.model_name,
                success=False,
                error="GROQ_API_KEY environment variable is not set.",
            )

        self._ensure_client(api_key)

        last_error: Optional[str] = None
        delay = self.retry_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                chat_completion = self._client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        }
                    ],
                    model=self.model_name,
                    temperature=self.temperature,
                )
                
                response_text = chat_completion.choices[0].message.content
                logger.info(f"Groq responded successfully on attempt {attempt}.")
                
                return LLMResponse(
                    text=response_text.strip(),
                    model=self.model_name,
                    success=True,
                    attempts=attempt,
                )

            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    f"Groq API error (attempt {attempt}/{self.max_retries}): {exc}"
                )
                if attempt < self.max_retries:
                    time.sleep(delay)
                    delay *= 2  # Exponential back-off

        return LLMResponse(
            text="",
            model=self.model_name,
            success=False,
            error=f"All {self.max_retries} attempts failed. Last error: {last_error}",
            attempts=self.max_retries,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _ensure_client(self, api_key: str):
        """Lazily initialize the Groq client."""
        if self._client is not None:
            return
        try:
            from groq import Groq
            self._client = Groq(api_key=api_key)
            logger.info(f"Groq client (model: '{self.model_name}') initialised.")
        except ImportError as e:
            raise RuntimeError(
                "groq package not installed. Run: pip install groq"
            ) from e
