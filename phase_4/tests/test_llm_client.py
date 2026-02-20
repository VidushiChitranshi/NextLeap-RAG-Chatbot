"""
Unit tests for phase_4/llm_client.py (GroqClient + LLMResponse)

The groq SDK is fully mocked — no API keys required.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, call


# ── Inject a mock for groq before importing the client ────────────────────

mock_groq_sdk = MagicMock()
sys.modules["groq"] = mock_groq_sdk

from phase_4.llm_client import GroqClient, LLMResponse  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────────

def make_client(**kwargs):
    """Return a fresh GroqClient with retries disabled by default."""
    defaults = {"max_retries": 1, "retry_delay": 0}
    defaults.update(kwargs)
    return GroqClient(**defaults)


def mock_groq_response(text: str):
    """Build a mock groq client whose chat.completions.create returns text."""
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = text
    
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    
    mock_groq_sdk.Groq.return_value = mock_client_instance
    return mock_client_instance


# ── Tests: LLMResponse ─────────────────────────────────────────────────────

class TestLLMResponse:
    def test_bool_true_when_success(self):
        r = LLMResponse(text="hello", model="llama", success=True)
        assert bool(r) is True

    def test_bool_false_when_failure(self):
        r = LLMResponse(text="", model="llama", success=False)
        assert bool(r) is False

    def test_has_expected_fields(self):
        r = LLMResponse(text="hi", model="llama-3.3-70b", success=True, attempts=2)
        assert r.text == "hi"
        assert r.model == "llama-3.3-70b"
        assert r.attempts == 2
        assert r.error is None


# ── Tests: GroqClient — no API key ────────────────────────────────────────

class TestGroqClientNoApiKey:
    def test_returns_failure_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        client = make_client()
        result = client.generate("system", "user")
        assert result.success is False
        assert "GROQ_API_KEY" in result.error

    def test_no_client_init_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        mock_groq_sdk.Groq.reset_mock()
        client = make_client()
        client.generate("sys", "usr")
        mock_groq_sdk.Groq.assert_not_called()


# ── Tests: GroqClient — successful call ───────────────────────────────────

class TestGroqClientSuccess:
    def test_returns_success_response(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_response("The fee is INR 36,999.")
        client = make_client()
        result = client.generate("system prompt", "user message")
        assert result.success is True
        assert result.text == "The fee is INR 36,999."

    def test_model_name_in_response(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_response("answer")
        client = GroqClient(model_name="mixtral-8x7b", max_retries=1, retry_delay=0)
        result = client.generate("sys", "usr")
        assert result.model == "mixtral-8x7b"

    def test_attempts_is_one_on_first_try(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_response("OK")
        client = make_client()
        result = client.generate("sys", "usr")
        assert result.attempts == 1

    def test_groq_init_with_api_key(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "test-key-xyz")
        mock_groq_sdk.Groq.reset_mock()
        mock_groq_response("hi")
        client = make_client()
        client.generate("sys", "usr")
        mock_groq_sdk.Groq.assert_called_once_with(api_key="test-key-xyz")

    def test_client_lazy_init_only_once(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_sdk.Groq.reset_mock()
        mock_groq_response("resp")
        client = make_client()
        client.generate("sys", "usr")
        client.generate("sys", "usr 2")
        # Groq client should only be created once
        assert mock_groq_sdk.Groq.call_count == 1


# ── Tests: GroqClient — retry logic ───────────────────────────────────────

class TestGroqClientRetry:
    def test_retries_on_exception(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_sdk.Groq.reset_mock()

        # Build mock response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Success after retries"
        
        mock_client_instance = MagicMock()
        mock_groq_sdk.Groq.return_value = mock_client_instance

        # Fail twice, succeed on third
        mock_client_instance.chat.completions.create.side_effect = [
            Exception("rate limit"),
            Exception("rate limit"),
            mock_completion,
        ]

        client = GroqClient(max_retries=3, retry_delay=0)
        result = client.generate("sys", "usr")
        assert result.success is True
        assert result.attempts == 3
        assert result.text == "Success after retries"

    def test_all_retries_exhausted_returns_failure(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "fake-key")
        mock_groq_sdk.Groq.reset_mock()

        mock_client_instance = MagicMock()
        mock_groq_sdk.Groq.return_value = mock_client_instance
        mock_client_instance.chat.completions.create.side_effect = Exception("persistent error")

        client = GroqClient(max_retries=3, retry_delay=0)
        result = client.generate("sys", "usr")
        assert result.success is False
        assert result.attempts == 3
        assert "persistent error" in result.error
