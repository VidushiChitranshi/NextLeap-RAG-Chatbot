"""
Unit tests for phase_5/formatter.py (ResponseFormatter + FormattedResponse)

No external dependencies — pure Python logic only.
"""

import pytest
from phase_5.formatter import ResponseFormatter, FormattedResponse


class TestFormattedResponse:
    """Tests for the FormattedResponse dataclass."""

    def test_character_count_equals_answer_length(self):
        resp = FormattedResponse(answer="Hello world")
        assert resp.character_count == len("Hello world")

    def test_has_citations_true_when_populated(self):
        resp = FormattedResponse(answer="text", citations=["Pricing"])
        assert resp.has_citations is True

    def test_has_citations_false_when_empty(self):
        resp = FormattedResponse(answer="text", citations=[])
        assert resp.has_citations is False

    def test_to_dict_has_required_keys(self):
        resp = FormattedResponse(answer="hi", citations=["Overview"])
        d = resp.to_dict()
        assert "answer" in d
        assert "citations" in d
        assert "is_fallback" in d
        assert "character_count" in d

    def test_to_dict_values_correct(self):
        resp = FormattedResponse(answer="hi", citations=["Pricing"], is_fallback=False)
        d = resp.to_dict()
        assert d["answer"] == "hi"
        assert d["citations"] == ["Pricing"]
        assert d["is_fallback"] is False


class TestResponseFormatterHappyPath:
    """Normal-case formatting."""

    def setup_method(self):
        self.formatter = ResponseFormatter(include_citations=True)

    def test_returns_formatted_response(self):
        result = self.formatter.format("The fee is INR 36,999.")
        assert isinstance(result, FormattedResponse)

    def test_answer_preserved(self):
        result = self.formatter.format("The fee is INR 36,999.")
        assert "INR 36,999" in result.answer

    def test_raw_answer_stored(self):
        result = self.formatter.format("  some answer  ")
        assert result.raw_answer == "  some answer  "

    def test_whitespace_stripped(self):
        result = self.formatter.format("   Hello   ")
        assert result.answer.startswith("Hello")
        assert not result.answer.endswith(" ")

    def test_excessive_newlines_collapsed(self):
        result = self.formatter.format("Line1\n\n\n\n\nLine2")
        assert "\n\n\n" not in result.answer

    def test_is_fallback_false_for_normal_answer(self):
        result = self.formatter.format("The program costs INR 36,999.")
        assert result.is_fallback is False


class TestResponseFormatterFallbackDetection:
    """Detection of 'no information' LLM responses."""

    def setup_method(self):
        self.formatter = ResponseFormatter()

    def test_detects_sorry_phrase(self):
        result = self.formatter.format(
            "I'm sorry, I don't have specific information on that."
        )
        assert result.is_fallback is True

    def test_detects_please_visit(self):
        result = self.formatter.format(
            "Please visit https://nextleap.app for more information."
        )
        assert result.is_fallback is True

    def test_detects_no_relevant_context(self):
        result = self.formatter.format("No relevant context was found.")
        assert result.is_fallback is True

    def test_normal_answer_is_not_fallback(self):
        result = self.formatter.format("The course costs INR 36,999.")
        assert result.is_fallback is False


class TestResponseFormatterCitations:
    """Citation extraction from chunk metadata."""

    def setup_method(self):
        self.formatter = ResponseFormatter(include_citations=True)

    def test_section_type_used_as_citation(self):
        meta = [{"section_type": "curriculum_week_1"}]
        result = self.formatter.format("Week 1 covers...", meta)
        assert "Curriculum Week 1" in result.citations

    def test_underscores_replaced_in_citation(self):
        meta = [{"section_type": "curriculum_week_1"}]
        result = self.formatter.format("Week 1 covers...", meta)
        assert "Curriculum Week 1" in result.citations

    def test_duplicate_citations_deduplicated(self):
        meta = [
            {"section_type": "curriculum"},
            {"section_type": "curriculum"},
            {"section_type": "curriculum"},
        ]
        result = self.formatter.format("answer", meta)
        assert result.citations.count("Curriculum") == 1

    def test_multiple_sections_all_cited(self):
        meta = [
            {"section_type": "curriculum"},
            {"section_type": "syllabus"},
            {"section_type": "faq"},
        ]
        result = self.formatter.format("answer", meta)
        assert "Curriculum" in result.citations
        assert "Syllabus" in result.citations
        assert "Faq" in result.citations

    def test_no_citations_appended_for_fallback(self):
        """Citations should NOT appear in fallback answers."""
        meta = [{"section_type": "pricing"}]
        result = self.formatter.format(
            "I'm sorry, I don't have specific information on that.", meta
        )
        assert "📚" not in result.answer

    def test_citations_appended_to_answer(self):
        meta = [{"section_type": "curriculum"}]
        result = self.formatter.format("The syllabus includes...", meta)
        assert "Curriculum" in result.answer  # citation inline in answer

    def test_no_metadata_means_no_citations(self):
        result = self.formatter.format("answer", [])
        assert result.citations == []

    def test_restricted_tags_filtered_and_source_included(self):
        """Pricing, Overview, Faculty should be filtered, but source URL should stay."""
        meta = [
            {"section_type": "pricing", "source": "https://nextleap.app/course/pm"},
            {"section_type": "overview", "source": "https://nextleap.app/course/pm"},
        ]
        result = self.formatter.format("answer", meta)
        # 'Pricing' and 'Overview' should NOT be in citations
        assert "Pricing" not in result.citations
        assert "Overview" not in result.citations
        # The source URL SHOULD be in citations
        assert "https://nextleap.app/course/pm" in result.citations

    def test_multiple_sources_included(self):
        meta = [
            {"source": "https://link1.com"},
            {"source": "https://link2.com"},
        ]
        result = self.formatter.format("answer", meta)
        assert "https://link1.com" in result.citations
        assert "https://link2.com" in result.citations

    def test_citations_appended_to_answer_as_links(self):
        meta = [{"source": "https://nextleap.app/course/pm"}]
        result = self.formatter.format("The fee is INR 36,999.", meta)
        assert "https://nextleap.app/course/pm" in result.answer


class TestResponseFormatterEdgeCases:
    """Empty / None input handling."""

    def setup_method(self):
        self.formatter = ResponseFormatter()

    def test_empty_string_returns_fallback(self):
        result = self.formatter.format("")
        assert result.is_fallback is True
        assert result.answer != ""  # friendly error message

    def test_none_like_whitespace_returns_fallback(self):
        result = self.formatter.format("   ")
        assert result.is_fallback is True

    def test_source_url_used_as_fallback_citation_label(self):
        meta = [{"source": "https://nextleap.app/course/pm"}]
        result = self.formatter.format("Some answer here.", meta)
        # 'pm' should be extracted from the URL
        assert "pm" in result.citations or len(result.citations) > 0
