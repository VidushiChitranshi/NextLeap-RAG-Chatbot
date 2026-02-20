"""
Unit tests for phase_4/prompt_builder.py (PromptBuilder + BuiltPrompt)

No external dependencies — pure Python logic tests.
"""

import pytest
from phase_4.prompt_builder import PromptBuilder, BuiltPrompt


class TestBuiltPrompt:
    """Tests for the BuiltPrompt dataclass."""

    def test_as_single_string_combines_system_and_user(self):
        bp = BuiltPrompt(
            system_prompt="System: be helpful",
            user_message="User: what is the fee?",
            has_context=True,
        )
        combined = bp.as_single_string()
        assert "System: be helpful" in combined
        assert "User: what is the fee?" in combined

    def test_as_single_string_custom_separator(self):
        bp = BuiltPrompt(
            system_prompt="SYS", user_message="USR", has_context=False
        )
        result = bp.as_single_string(separator=" ||| ")
        assert result == "SYS ||| USR"

    def test_has_context_reflects_blocks_presence(self):
        builder = PromptBuilder()
        with_ctx = builder.build("query", ["Block A"])
        no_ctx = builder.build("query", [])
        assert with_ctx.has_context is True
        assert no_ctx.has_context is False


class TestPromptBuilderValidInput:
    """Happy-path tests for PromptBuilder.build()."""

    def setup_method(self):
        self.builder = PromptBuilder()

    def test_returns_built_prompt(self):
        result = self.builder.build("what is the fee?", ["Pricing: INR 36999"])
        assert isinstance(result, BuiltPrompt)

    def test_system_prompt_present(self):
        result = self.builder.build("query", [])
        assert len(result.system_prompt) > 0

    def test_context_blocks_numbered(self):
        result = self.builder.build(
            "query",
            ["Block one content", "Block two content"],
        )
        assert "[Block 1]" in result.user_message
        assert "[Block 2]" in result.user_message

    def test_query_in_user_message(self):
        result = self.builder.build("who are the mentors?", ["Some context"])
        assert "who are the mentors?" in result.user_message

    def test_no_context_message_indicates_no_context(self):
        result = self.builder.build("something", [])
        assert "No relevant context" in result.user_message

    def test_context_content_in_user_message(self):
        result = self.builder.build("query", ["Pricing: INR 36999"])
        assert "INR 36999" in result.user_message

    def test_none_context_treated_as_empty(self):
        result = self.builder.build("query", None)
        assert result.has_context is False

    def test_multiple_blocks_all_present(self):
        blocks = ["Chunk A", "Chunk B", "Chunk C"]
        result = self.builder.build("q", blocks)
        for block in blocks:
            assert block in result.user_message

    def test_custom_system_prompt_used(self):
        custom = "You are a test bot."
        builder = PromptBuilder(system_prompt=custom)
        result = builder.build("query", [])
        assert result.system_prompt == custom


class TestPromptBuilderEdgeCases:
    """Error and edge-case handling."""

    def setup_method(self):
        self.builder = PromptBuilder()

    def test_empty_query_raises(self):
        with pytest.raises(ValueError):
            self.builder.build("", ["context"])

    def test_whitespace_only_query_raises(self):
        with pytest.raises(ValueError):
            self.builder.build("   ", ["context"])

    def test_empty_string_in_blocks_not_added_as_block_label(self):
        # Empty strings in blocks should not crash
        result = self.builder.build("query", ["", "Real content"])
        # At minimum the real content should appear
        assert "Real content" in result.user_message


class TestPromptBuilderTruncation:
    """Context truncation when max_context_chars is set."""

    def test_long_context_truncated(self):
        builder = PromptBuilder(max_context_chars=50)
        long_block = "A" * 200
        result = builder.build("query", [long_block])
        assert "[truncated]" in result.user_message

    def test_short_context_not_truncated(self):
        builder = PromptBuilder(max_context_chars=500)
        result = builder.build("query", ["short block"])
        assert "[truncated]" not in result.user_message

    def test_no_truncation_when_disabled(self):
        builder = PromptBuilder(max_context_chars=None)
        long_block = "B" * 10_000
        result = builder.build("query", [long_block])
        assert "[truncated]" not in result.user_message
        assert "B" * 100 in result.user_message
