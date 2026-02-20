"""
Unit tests for phase_2/processor.py (DataProcessor)

Tests the DataProcessor class which converts raw JSON course data
into LangChain Documents. These tests use no external dependencies
(no langchain API calls), so they run without any API keys.
"""

import json
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

# --- We mock langchain_core before importing phase_2 to avoid installing it ---
import sys

# Create a lightweight mock for langchain_core.documents.Document
class MockDocument:
    """Minimal stand-in for langchain_core.documents.Document"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"MockDocument(content={self.page_content[:40]!r}, metadata={self.metadata})"


# Inject mocks into sys.modules BEFORE importing phase_2
langchain_core_mock = MagicMock()
langchain_core_mock.documents.Document = MockDocument
sys.modules.setdefault("langchain_core", langchain_core_mock)
sys.modules.setdefault("langchain_core.documents", langchain_core_mock.documents)

from phase_2.processor import DataProcessor  # noqa: E402 — import after mock setup


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

MINIMAL_COURSE = {
    "metadata": {"source_url": "https://nextleap.app/course/pm"},
    "course": {
        "title": "Product Management Fellowship",
        "duration_weeks": 16,
        "fellowship_months": 4,
        "live_class_hours": 100,
        "placement_support_years": 1,
        "certification_awarded": "Yes"
    },
    "pricing": {"display": "INR 36,999", "amount": 36999},
    "cohort": {"id": 47, "start_date": "2026-03-07", "status": "OPEN"},
    "faculty": {
        "instructors": [
            {"name": "Devansh Jain", "designation": "CEO", "company": "NextLeap"}
        ],
        "mentors": [
            {"name": "Akash Agrawal", "designation": "PM", "company": "Google"}
        ]
    },
    "curriculum": []
}

FULL_COURSE_WITH_CURRICULUM = {
    **MINIMAL_COURSE,
    "curriculum": [
        {"title": "Week 1: Intro to PM", "content": "Basics of product management."},
        {"title": "Week 2: User Research", "content": "How to conduct user interviews."},
    ]
}


# ─────────────────────────────────────────────
# TestDataProcessorLoadData
# ─────────────────────────────────────────────

class TestDataProcessorLoadData:
    """Tests for DataProcessor.load_data()"""

    def setup_method(self):
        self.processor = DataProcessor()

    def test_load_valid_json_file(self, tmp_path):
        """Should load a valid JSON file and return a dict."""
        data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = self.processor.load_data(str(json_file))

        assert result == data

    def test_load_raises_on_missing_file(self):
        """Should raise an exception when the file does not exist."""
        with pytest.raises(Exception):
            self.processor.load_data("nonexistent_file_xyz.json")

    def test_load_raises_on_invalid_json(self, tmp_path):
        """Should raise an exception when the file contains invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ not valid json !!!", encoding="utf-8")

        with pytest.raises(Exception):
            self.processor.load_data(str(bad_file))

    def test_load_empty_object_json(self, tmp_path):
        """Should handle an empty JSON object without error."""
        json_file = tmp_path / "empty.json"
        json_file.write_text("{}", encoding="utf-8")

        result = self.processor.load_data(str(json_file))
        assert result == {}


# ─────────────────────────────────────────────
# TestDataProcessorProcessCourse
# ─────────────────────────────────────────────

class TestDataProcessorProcessCourse:
    """Tests for DataProcessor.process_course()"""

    def setup_method(self):
        self.processor = DataProcessor()

    def test_returns_list_of_documents(self):
        """process_course should always return a list."""
        result = self.processor.process_course(MINIMAL_COURSE)
        assert isinstance(result, list)

    def test_minimum_documents_produced(self):
        """Should produce at least 2 docs (overview + pricing) for any valid course."""
        result = self.processor.process_course(MINIMAL_COURSE)
        assert len(result) >= 2

    def test_overview_document_present(self):
        """The first document should contain the course title."""
        result = self.processor.process_course(MINIMAL_COURSE)
        overview = result[0]
        assert "Product Management Fellowship" in overview.page_content

    def test_overview_document_metadata(self):
        """Overview document should have correct metadata."""
        result = self.processor.process_course(MINIMAL_COURSE)
        overview = result[0]
        assert overview.metadata["section_type"] == "overview"
        assert overview.metadata["source"] == "https://nextleap.app/course/pm"

    def test_pricing_document_present(self):
        """Should produce a pricing document containing price and cohort data."""
        result = self.processor.process_course(MINIMAL_COURSE)
        pricing_docs = [d for d in result if d.metadata.get("section_type") == "pricing"]
        assert len(pricing_docs) == 1
        assert "INR 36,999" in pricing_docs[0].page_content
        assert "OPEN" in pricing_docs[0].page_content

    def test_instructor_document_present(self):
        """Should produce an instructor document when instructors are present."""
        result = self.processor.process_course(MINIMAL_COURSE)
        instructor_docs = [
            d for d in result
            if d.metadata.get("section_type") == "faculty"
            and d.metadata.get("subtype") == "instructors"
        ]
        assert len(instructor_docs) == 1
        assert "Devansh Jain" in instructor_docs[0].page_content

    def test_mentor_document_present(self):
        """Should produce a mentor document when mentors are present."""
        result = self.processor.process_course(MINIMAL_COURSE)
        mentor_docs = [
            d for d in result
            if d.metadata.get("section_type") == "faculty"
            and d.metadata.get("subtype") == "mentors"
        ]
        assert len(mentor_docs) == 1
        assert "Akash Agrawal" in mentor_docs[0].page_content

    def test_no_instructor_doc_when_empty(self):
        """Should NOT produce an instructor document when the list is empty."""
        data = {**MINIMAL_COURSE, "faculty": {"instructors": [], "mentors": []}}
        result = self.processor.process_course(data)
        instructor_docs = [
            d for d in result if d.metadata.get("subtype") == "instructors"
        ]
        assert len(instructor_docs) == 0

    def test_curriculum_documents_generated(self):
        """Should produce one document per curriculum module."""
        result = self.processor.process_course(FULL_COURSE_WITH_CURRICULUM)
        curriculum_docs = [
            d for d in result if d.metadata.get("section_type") == "curriculum"
        ]
        assert len(curriculum_docs) == 2
        titles = [d.page_content for d in curriculum_docs]
        assert any("Week 1: Intro to PM" in t for t in titles)
        assert any("Week 2: User Research" in t for t in titles)

    def test_empty_data_returns_minimal_docs(self):
        """Should handle completely empty data gracefully (returns overview + pricing)."""
        result = self.processor.process_course({})
        # Should not raise; overview + pricing always produced
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_overview_contains_all_key_fields(self):
        """Overview document should include duration, certification, and placement."""
        result = self.processor.process_course(MINIMAL_COURSE)
        content = result[0].page_content
        assert "16 weeks" in content
        assert "4 months" in content
        assert "1 year" in content
        assert "Yes" in content

    def test_multiple_instructors_all_appear(self):
        """All instructors should appear in the instructor document."""
        data = {
            **MINIMAL_COURSE,
            "faculty": {
                "instructors": [
                    {"name": "Alice", "designation": "PM", "company": "X"},
                    {"name": "Bob", "designation": "CTO", "company": "Y"},
                ],
                "mentors": []
            }
        }
        result = self.processor.process_course(data)
        instructor_docs = [
            d for d in result if d.metadata.get("subtype") == "instructors"
        ]
        content = instructor_docs[0].page_content
        assert "Alice" in content
        assert "Bob" in content

    def test_source_url_propagated_to_all_docs(self):
        """Every document should carry the source_url in its metadata."""
        result = self.processor.process_course(MINIMAL_COURSE)
        for doc in result:
            assert doc.metadata.get("source") == "https://nextleap.app/course/pm"
