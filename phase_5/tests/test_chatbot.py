"""
Unit tests for phase_5/chatbot.py (Chatbot + ChatReply)

All Phase 3 and Phase 4 dependencies are mocked — no external calls.
"""

import pytest
from unittest.mock import MagicMock
from phase_5.chatbot import Chatbot, ChatReply
from phase_5.formatter import ResponseFormatter
from phase_5.history import ConversationHistory


# ── Helpers ────────────────────────────────────────────────────────────────

def make_retrieval_result(content: str, metadata: dict = None, score: float = 0.9):
    result = MagicMock()
    result.content = content
    result.score = score
    result.metadata = metadata or {"section_type": "overview"}
    return result


def make_pipeline_output(
    success: bool = True,
    original_query: str = "What is the fee?",
    cleaned_query: str = "what is the fee?",
    context_string: str = "Pricing: INR 36,999",
    error: str = None,
    results=None,
):
    out = MagicMock()
    out.success = success
    out.original_query = original_query
    out.cleaned_query = cleaned_query
    out.context_string = context_string if success else ""
    out.error = error
    out.results = results or [
        make_retrieval_result("Pricing: INR 36,999", {"section_type": "pricing"})
    ]
    return out


def make_gen_response(text: str = "The fee is INR 36,999.", success: bool = True, error: str = None):
    resp = MagicMock()
    resp.success = success
    resp.answer = text if success else ""
    resp.error = error
    return resp


def make_chatbot(
    pipeline_output=None,
    gen_text: str = "The fee is INR 36,999.",
    gen_success: bool = True,
):
    pipeline = MagicMock()
    pipeline.run.return_value = pipeline_output or make_pipeline_output()

    generator = MagicMock()
    generator.answer_from_pipeline.return_value = make_gen_response(gen_text, gen_success)

    bot = Chatbot(
        retrieval_pipeline=pipeline,
        response_generator=generator,
    )
    return bot, pipeline, generator


# ── Tests: ChatReply ──────────────────────────────────────────────────────

class TestChatReply:
    def test_success_true_by_default(self):
        reply = ChatReply(query="q", answer="a")
        assert reply.success is True

    def test_error_is_none_by_default(self):
        reply = ChatReply(query="q", answer="a")
        assert reply.error is None

    def test_is_fallback_false_by_default(self):
        reply = ChatReply(query="q", answer="a")
        assert reply.is_fallback is False


# ── Tests: Chatbot.chat — happy path ──────────────────────────────────────

class TestChatbotChatSuccess:
    def test_returns_chat_reply(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("What is the fee?")
        assert isinstance(reply, ChatReply)

    def test_query_preserved(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("What is the fee?")
        assert reply.query == "What is the fee?"

    def test_answer_populated(self):
        bot, _, _ = make_chatbot(gen_text="The fee is INR 36,999.")
        reply = bot.chat("fee question")
        assert "INR 36,999" in reply.answer

    def test_success_is_true(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("valid question here")
        assert reply.success is True

    def test_error_is_none_on_success(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("question")
        assert reply.error is None

    def test_turn_stored_in_history(self):
        bot, _, _ = make_chatbot()
        bot.chat("first question")
        bot.chat("second question")
        assert bot.turn_count == 2

    def test_turn_attached_to_reply(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("question")
        assert reply.turn is not None

    def test_pipeline_run_called_with_query(self):
        bot, pipeline, _ = make_chatbot()
        bot.chat("What is the deadline?")
        pipeline.run.assert_called_once_with("What is the deadline?")

    def test_generator_called_with_pipeline_output(self):
        p_out = make_pipeline_output()
        bot, pipeline, generator = make_chatbot(pipeline_output=p_out)
        bot.chat("question")
        generator.answer_from_pipeline.assert_called_once_with(p_out)


# ── Tests: Chatbot.chat — fallback ────────────────────────────────────────

class TestChatbotChatFallback:
    def test_fallback_answer_detected(self):
        bot, _, _ = make_chatbot(
            gen_text="I'm sorry, I don't have specific information on that."
        )
        reply = bot.chat("obscure question")
        assert reply.is_fallback is True

    def test_fallback_still_success(self):
        """A fallback answer is a valid response — success should be True."""
        bot, _, _ = make_chatbot(
            gen_text="I'm sorry, I don't have specific information on that."
        )
        reply = bot.chat("obscure question")
        assert reply.success is True

    def test_fallback_recorded_in_history(self):
        bot, _, _ = make_chatbot(
            gen_text="I'm sorry, I don't have specific information on that."
        )
        bot.chat("obscure question")
        last = bot.history.last_turn
        assert last.is_fallback is True


# ── Tests: Chatbot.chat — LLM failure ─────────────────────────────────────

class TestChatbotChatLLMFailure:
    def test_llm_failure_sets_success_false(self):
        bot, _, _ = make_chatbot(gen_success=False)
        reply = bot.chat("question")
        assert reply.success is False

    def test_llm_failure_sets_error(self):
        pipeline = MagicMock()
        pipeline.run.return_value = make_pipeline_output()
        generator = MagicMock()
        generator.answer_from_pipeline.return_value = make_gen_response(
            success=False, error="API timeout"
        )
        bot = Chatbot(retrieval_pipeline=pipeline, response_generator=generator)
        reply = bot.chat("question")
        assert reply.error is not None

    def test_llm_failure_answer_is_empty(self):
        bot, _, _ = make_chatbot(gen_success=False)
        reply = bot.chat("question")
        assert reply.answer == ""

    def test_failed_turn_not_stored(self):
        bot, _, _ = make_chatbot(gen_success=False)
        bot.chat("failing question")
        assert bot.turn_count == 0


# ── Tests: Chatbot.chat — edge cases ─────────────────────────────────────

class TestChatbotChatEdgeCases:
    def test_empty_query_returns_failure(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("")
        assert reply.success is False
        assert reply.error is not None

    def test_whitespace_only_returns_failure(self):
        bot, _, _ = make_chatbot()
        reply = bot.chat("   ")
        assert reply.success is False


# ── Tests: Chatbot history helpers ────────────────────────────────────────

class TestChatbotHistoryHelpers:
    def setup_method(self):
        self.bot, _, _ = make_chatbot()

    def test_get_history_returns_turns(self):
        self.bot.chat("q1")
        self.bot.chat("q2")
        history = self.bot.get_history(5)
        assert len(history) == 2

    def test_clear_history_resets_count(self):
        self.bot.chat("q1")
        self.bot.clear_history()
        assert self.bot.turn_count == 0

    def test_turn_count_tracks_successful_chats(self):
        self.bot.chat("q1")
        self.bot.chat("q2")
        self.bot.chat("q3")
        assert self.bot.turn_count == 3


# ── Tests: Chatbot uses custom formatter and history ─────────────────────

class TestChatbotCustomDependencies:
    def test_custom_formatter_used(self):
        custom_formatter = ResponseFormatter(include_citations=False)
        p_out = make_pipeline_output()
        pipeline = MagicMock()
        pipeline.run.return_value = p_out
        generator = MagicMock()
        generator.answer_from_pipeline.return_value = make_gen_response("answer")

        bot = Chatbot(pipeline, generator, formatter=custom_formatter)
        reply = bot.chat("question")
        # Citations should not appear since include_citations=False
        assert "📚" not in reply.answer

    def test_custom_history_used(self):
        custom_history = ConversationHistory(max_turns=2)
        bot, _, _ = make_chatbot()
        bot.history = custom_history
        bot.chat("q1")
        bot.chat("q2")
        assert bot.history.turn_count == 2
