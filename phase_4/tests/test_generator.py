"""
Unit tests for phase_4/generator.py (ResponseGenerator + GeneratorResponse)

LLM calls are fully mocked — no API keys or real Groq calls.
"""

import pytest
from unittest.mock import MagicMock, patch
from phase_4.generator import ResponseGenerator, GeneratorResponse
from phase_4.llm_client import LLMResponse
from phase_4.prompt_builder import BuiltPrompt


# ── Helpers ────────────────────────────────────────────────────────────────

def make_llm_client(text: str = "Mock answer.", success: bool = True, error: str = None):
    """Return a mock GroqClient."""
    client = MagicMock()
    client.generate.return_value = LLMResponse(
        text=text if success else "",
        model="llama3-70b-8192",
        success=success,
        error=error,
        attempts=1,
    )
    return client


def make_pipeline_output(
    success: bool = True,
    original_query: str = "What is the fee?",
    cleaned_query: str = "what is the fee?",
    context_string: str = "Pricing: INR 36999\n\n---\n\nStarts: March 2026",
    error: str = None,
):
    """Return a mock Phase 3 PipelineOutput."""
    out = MagicMock()
    out.success = success
    out.original_query = original_query
    out.cleaned_query = cleaned_query
    out.context_string = context_string if success else ""
    out.error = error
    return out


# ── Tests: GeneratorResponse ───────────────────────────────────────────────

class TestGeneratorResponse:
    def test_success_true_when_populated(self):
        resp = GeneratorResponse(query="q", answer="A", success=True)
        assert resp.success is True

    def test_success_false_by_default(self):
        resp = GeneratorResponse(query="q", answer="")
        assert resp.success is False

    def test_error_none_by_default(self):
        resp = GeneratorResponse(query="q", answer="text", success=True)
        assert resp.error is None


# ── Tests: ResponseGenerator.answer — happy path ──────────────────────────

class TestResponseGeneratorAnswerSuccess:
    def _make(self, text="Mock answer."):
        client = make_llm_client(text=text)
        return ResponseGenerator(llm_client=client), client

    def test_returns_generator_response(self):
        gen, _ = self._make()
        result = gen.answer("what is the fee?", ["Pricing: INR 36,999"])
        assert isinstance(result, GeneratorResponse)

    def test_answer_text_populated(self):
        gen, _ = self._make("The fee is INR 36,999.")
        result = gen.answer("fee?", ["Pricing: INR 36,999"])
        assert result.answer == "The fee is INR 36,999."

    def test_success_is_true(self):
        gen, _ = self._make()
        result = gen.answer("mentors?", ["Mentor info here"])
        assert result.success is True

    def test_error_is_none(self):
        gen, _ = self._make()
        result = gen.answer("query", ["context"])
        assert result.error is None

    def test_query_preserved(self):
        gen, _ = self._make()
        result = gen.answer("who are the instructors?", [])
        assert result.query == "who are the instructors?"

    def test_prompt_attached_to_response(self):
        gen, _ = self._make()
        result = gen.answer("query?", ["some context"])
        assert isinstance(result.prompt, BuiltPrompt)

    def test_llm_response_attached(self):
        gen, _ = self._make()
        result = gen.answer("query?", ["ctx"])
        assert isinstance(result.llm_response, LLMResponse)

    def test_llm_called_with_system_and_user(self):
        gen, client = self._make()
        gen.answer("query", ["block"])
        client.generate.assert_called_once()
        args = client.generate.call_args
        assert args[1]["system_prompt"] or args[0][0]  # system_prompt passed
        assert args[1]["user_message"] or args[0][1]   # user_message passed

    def test_no_context_blocks_still_succeeds(self):
        gen, _ = self._make("Sorry, no context but answering anyway.")
        result = gen.answer("something", [])
        assert result.success is True


# ── Tests: ResponseGenerator.answer — failure cases ──────────────────────

class TestResponseGeneratorAnswerFailure:
    def test_empty_query_returns_failure(self):
        gen = ResponseGenerator(llm_client=make_llm_client())
        result = gen.answer("", ["ctx"])
        assert result.success is False
        assert result.error is not None

    def test_whitespace_query_returns_failure(self):
        gen = ResponseGenerator(llm_client=make_llm_client())
        result = gen.answer("   ", ["ctx"])
        assert result.success is False

    def test_llm_failure_propagated(self):
        client = make_llm_client(success=False, error="API timeout")
        gen = ResponseGenerator(llm_client=client)
        result = gen.answer("query?", ["ctx"])
        assert result.success is False
        assert "API timeout" in result.error

    def test_answer_empty_on_llm_failure(self):
        client = make_llm_client(success=False, error="oops")
        gen = ResponseGenerator(llm_client=client)
        result = gen.answer("q", ["c"])
        assert result.answer == ""


# ── Tests: answer_from_pipeline — happy path ──────────────────────────────

class TestAnswerFromPipelineSuccess:
    def test_returns_generator_response(self):
        client = make_llm_client("Here is the answer.")
        gen = ResponseGenerator(llm_client=client)
        output = make_pipeline_output()
        result = gen.answer_from_pipeline(output)
        assert isinstance(result, GeneratorResponse)

    def test_success_is_true(self):
        client = make_llm_client("Answer text")
        gen = ResponseGenerator(llm_client=client)
        result = gen.answer_from_pipeline(make_pipeline_output())
        assert result.success is True

    def test_context_blocks_split_from_context_string(self):
        """Context string with separator should be split into multiple blocks."""
        client = make_llm_client("ok")
        gen = ResponseGenerator(llm_client=client)
        output = make_pipeline_output(
            context_string="Block A\n\n---\n\nBlock B\n\n---\n\nBlock C"
        )
        result = gen.answer_from_pipeline(output)
        # 3 blocks → prompt should have [Block 1], [Block 2], [Block 3]
        assert "[Block 1]" in result.prompt.user_message
        assert "[Block 3]" in result.prompt.user_message


# ── Tests: answer_from_pipeline — Phase 3 failure ─────────────────────────

class TestAnswerFromPipelinePhase3Failure:
    def test_phase3_failure_forwarded(self):
        client = make_llm_client()
        gen = ResponseGenerator(llm_client=client)
        output = make_pipeline_output(success=False, error="No results found")
        result = gen.answer_from_pipeline(output)
        assert result.success is False
        assert "No results found" in result.error

    def test_llm_not_called_when_phase3_failed(self):
        client = make_llm_client()
        gen = ResponseGenerator(llm_client=client)
        output = make_pipeline_output(success=False, error="empty")
        gen.answer_from_pipeline(output)
        client.generate.assert_not_called()
