"""
Unit tests for phase_5/history.py (ConversationHistory + Turn)

Pure Python — no external dependencies.
"""

import pytest
from phase_5.history import ConversationHistory, Turn


class TestTurn:
    def test_has_expected_fields(self):
        turn = Turn(query="hi", answer="hello")
        assert turn.query == "hi"
        assert turn.answer == "hello"
        assert turn.is_fallback is False

    def test_timestamp_is_string(self):
        turn = Turn(query="q", answer="a")
        assert isinstance(turn.timestamp, str)
        assert len(turn.timestamp) > 0


class TestConversationHistoryInit:
    def test_starts_empty(self):
        h = ConversationHistory()
        assert h.is_empty is True
        assert h.turn_count == 0

    def test_last_turn_none_when_empty(self):
        h = ConversationHistory()
        assert h.last_turn is None

    def test_invalid_max_turns_raises(self):
        with pytest.raises(ValueError):
            ConversationHistory(max_turns=0)

    def test_negative_max_turns_raises(self):
        with pytest.raises(ValueError):
            ConversationHistory(max_turns=-5)


class TestConversationHistoryAdd:
    def setup_method(self):
        self.h = ConversationHistory(max_turns=5)

    def test_add_returns_turn(self):
        turn = self.h.add("hello?", "hi!")
        assert isinstance(turn, Turn)

    def test_turn_count_increments(self):
        self.h.add("q1", "a1")
        self.h.add("q2", "a2")
        assert self.h.turn_count == 2

    def test_is_empty_false_after_add(self):
        self.h.add("q", "a")
        assert self.h.is_empty is False

    def test_last_turn_updated(self):
        self.h.add("first", "first answer")
        self.h.add("second", "second answer")
        assert self.h.last_turn.query == "second"

    def test_is_fallback_stored(self):
        turn = self.h.add("q", "a", is_fallback=True)
        assert turn.is_fallback is True

    def test_rolling_window_trims_old_turns(self):
        h = ConversationHistory(max_turns=3)
        for i in range(5):
            h.add(f"q{i}", f"a{i}")
        assert h.turn_count == 3
        # The first two turns should be gone
        assert h.get_recent(10)[0].query == "q2"


class TestConversationHistoryGetRecent:
    def setup_method(self):
        self.h = ConversationHistory()
        for i in range(5):
            self.h.add(f"q{i}", f"a{i}")

    def test_get_recent_returns_correct_count(self):
        assert len(self.h.get_recent(3)) == 3

    def test_get_recent_returns_newest_last(self):
        recent = self.h.get_recent(2)
        assert recent[-1].query == "q4"

    def test_get_recent_zero_returns_empty(self):
        assert self.h.get_recent(0) == []

    def test_get_recent_exceeds_count_returns_all(self):
        assert len(self.h.get_recent(100)) == 5


class TestConversationHistoryClear:
    def test_clear_empties_history(self):
        h = ConversationHistory()
        h.add("q", "a")
        h.clear()
        assert h.is_empty

    def test_clear_resets_turn_count(self):
        h = ConversationHistory()
        h.add("q", "a")
        h.clear()
        assert h.turn_count == 0

    def test_add_after_clear_works(self):
        h = ConversationHistory()
        h.add("q", "a")
        h.clear()
        h.add("new q", "new a")
        assert h.turn_count == 1


class TestToPromptContext:
    def setup_method(self):
        self.h = ConversationHistory()
        self.h.add("What is the fee?", "The fee is INR 36,999.")
        self.h.add("When does it start?", "It starts in March 2026.")

    def test_returns_string(self):
        result = self.h.to_prompt_context()
        assert isinstance(result, str)

    def test_contains_queries(self):
        result = self.h.to_prompt_context(2)
        assert "What is the fee?" in result
        assert "When does it start?" in result

    def test_contains_answers(self):
        result = self.h.to_prompt_context(2)
        assert "INR 36,999" in result
        assert "March 2026" in result

    def test_empty_history_returns_empty_string(self):
        h = ConversationHistory()
        assert h.to_prompt_context() == ""

    def test_n_limits_included_turns(self):
        result = self.h.to_prompt_context(n=1)
        assert "What is the fee?" not in result
        assert "When does it start?" in result
