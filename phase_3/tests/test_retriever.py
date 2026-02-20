"""
Unit tests for phase_3/retriever.py (Retriever + RetrievalResult)

Uses a MagicMock VectorStore so no external packages are needed.
"""

import pytest
from unittest.mock import MagicMock
from phase_3.retriever import Retriever, RetrievalResult


# ── Helpers ────────────────────────────────────────────────────────────────

def make_mock_doc(content: str, metadata: dict = None):
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = metadata or {}
    return doc


def make_scored_store(pairs: list):
    """Return a mock store whose similarity_search_with_score returns pairs."""
    store = MagicMock(spec=["similarity_search_with_score"])
    store.similarity_search_with_score.return_value = pairs
    return store


def make_unscored_store(docs: list):
    """Return a mock store that only has query_similar (no scores)."""
    store = MagicMock(spec=["query_similar"])
    store.query_similar.return_value = docs
    return store


# ── Tests: RetrievalResult ─────────────────────────────────────────────────

class TestRetrievalResult:
    def test_has_expected_fields(self):
        r = RetrievalResult(content="hello", score=0.9, rank=1)
        assert r.content == "hello"
        assert r.score == 0.9
        assert r.rank == 1

    def test_metadata_defaults_to_empty_dict(self):
        r = RetrievalResult(content="text", score=None)
        assert r.metadata == {}

    def test_repr_contains_rank_and_content(self):
        r = RetrievalResult(content="Some content here", score=0.85, rank=2)
        rep = repr(r)
        assert "rank=2" in rep
        assert "0.850" in rep

    def test_repr_handles_none_score(self):
        r = RetrievalResult(content="text", score=None, rank=1)
        assert "N/A" in repr(r)


# ── Tests: Retriever — scored store ───────────────────────────────────────

class TestRetrieverScoredStore:
    def _make(self, pairs, top_k=5, threshold=None):
        store = make_scored_store(pairs)
        return Retriever(store, top_k=top_k, relevance_threshold=threshold), store

    def test_returns_results_in_order(self):
        pairs = [
            (make_mock_doc("Result A"), 0.95),
            (make_mock_doc("Result B"), 0.80),
        ]
        r, _ = self._make(pairs)
        results = r.retrieve("some query")
        assert results[0].content == "Result A"
        assert results[1].content == "Result B"

    def test_scores_assigned(self):
        pairs = [(make_mock_doc("Doc"), 0.88)]
        r, _ = self._make(pairs)
        results = r.retrieve("query")
        assert results[0].score == pytest.approx(0.88)

    def test_ranks_are_one_based(self):
        pairs = [(make_mock_doc(f"Doc {i}"), 0.9 - i * 0.1) for i in range(3)]
        r, _ = self._make(pairs)
        results = r.retrieve("q")
        assert [res.rank for res in results] == [1, 2, 3]

    def test_top_k_passed_to_store(self):
        store = make_scored_store([])
        r = Retriever(store, top_k=7)
        r.retrieve("query")
        store.similarity_search_with_score.assert_called_once_with("query", k=7)

    def test_threshold_filters_low_scores(self):
        pairs = [
            (make_mock_doc("Good"), 0.85),
            (make_mock_doc("Bad"), 0.45),  # below threshold
        ]
        r, _ = self._make(pairs, threshold=0.7)
        results = r.retrieve("query")
        assert len(results) == 1
        assert results[0].content == "Good"

    def test_all_fail_threshold_returns_empty(self):
        pairs = [(make_mock_doc("Weak"), 0.3)]
        r, _ = self._make(pairs, threshold=0.8)
        results = r.retrieve("query")
        assert results == []

    def test_no_threshold_keeps_all_results(self):
        pairs = [
            (make_mock_doc("A"), 0.1),
            (make_mock_doc("B"), 0.05),
        ]
        r, _ = self._make(pairs, threshold=None)
        results = r.retrieve("query")
        assert len(results) == 2

    def test_metadata_preserved(self):
        doc = make_mock_doc("text", metadata={"section_type": "pricing"})
        store = make_scored_store([(doc, 0.9)])
        r = Retriever(store)
        results = r.retrieve("pricing")
        assert results[0].metadata["section_type"] == "pricing"

    def test_store_exception_returns_empty(self):
        store = MagicMock(spec=["similarity_search_with_score"])
        store.similarity_search_with_score.side_effect = RuntimeError("DB crash")
        r = Retriever(store)
        results = r.retrieve("query")
        assert results == []


# ── Tests: Retriever — unscored fallback store ────────────────────────────

class TestRetrieverUnscoredStore:
    def test_falls_back_to_query_similar(self):
        docs = [make_mock_doc("Unscored doc")]
        store = make_unscored_store(docs)
        r = Retriever(store)
        results = r.retrieve("something")
        assert len(results) == 1
        assert results[0].score is None

    def test_threshold_ignored_when_no_scores(self):
        """With no scores, threshold filter must not drop anything."""
        docs = [make_mock_doc("Doc A"), make_mock_doc("Doc B")]
        store = make_unscored_store(docs)
        r = Retriever(store, relevance_threshold=0.99)
        results = r.retrieve("query")
        assert len(results) == 2


# ── Tests: Retriever — empty query ─────────────────────────────────────────

class TestRetrieverEmptyQuery:
    def test_empty_string_returns_empty(self):
        store = make_scored_store([])
        r = Retriever(store)
        assert r.retrieve("") == []

    def test_whitespace_only_returns_empty(self):
        store = make_scored_store([])
        r = Retriever(store)
        assert r.retrieve("   ") == []


# ── Tests: get_context_string ─────────────────────────────────────────────

class TestRetrieverGetContextString:
    def test_joins_results_with_default_separator(self):
        pairs = [
            (make_mock_doc("Block one."), 0.9),
            (make_mock_doc("Block two."), 0.8),
        ]
        store = make_scored_store(pairs)
        r = Retriever(store)
        ctx = r.get_context_string("query")
        assert "Block one." in ctx
        assert "Block two." in ctx
        assert "\n\n---\n\n" in ctx

    def test_returns_empty_string_when_no_results(self):
        store = make_scored_store([])
        r = Retriever(store)
        ctx = r.get_context_string("query")
        assert ctx == ""
