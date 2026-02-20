"""
Unit tests for phase_2/store.py (VectorStore)

VectorStore wraps ChromaDB and GoogleGenerativeAIEmbeddings.
We fully mock the external libraries so these tests run without
any API keys or installed vector-DB packages.
"""

import sys
import os
import shutil
import pytest
from unittest.mock import MagicMock, patch, call


# ── Inject all required mocks before importing phase_2 ─────────────────────

class MockDocument:
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}


# langchain_core
lc_core = MagicMock()
lc_core.documents.Document = MockDocument
sys.modules.setdefault("langchain_core", lc_core)
sys.modules.setdefault("langchain_core.documents", lc_core.documents)

# langchain_chroma
mock_chroma_instance = MagicMock()
mock_chroma_class = MagicMock(return_value=mock_chroma_instance)
lc_chroma = MagicMock()
lc_chroma.Chroma = mock_chroma_class
sys.modules["langchain_chroma"] = lc_chroma

# langchain_google_genai
mock_embeddings_instance = MagicMock()
mock_embeddings_class = MagicMock(return_value=mock_embeddings_instance)
lc_google = MagicMock()
lc_google.GoogleGenerativeAIEmbeddings = mock_embeddings_class
sys.modules["langchain_google_genai"] = lc_google

from phase_2.store import VectorStore  # noqa: E402


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks before every test."""
    mock_chroma_instance.reset_mock()
    mock_chroma_class.reset_mock()
    mock_embeddings_class.reset_mock()
    yield


@pytest.fixture
def store(monkeypatch):
    """Return a VectorStore with GOOGLE_API_KEY set."""
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-test-key-12345")
    mock_chroma_class.return_value = mock_chroma_instance
    return VectorStore(persist_directory="data/test_chroma_db")


# ── Tests: Initialization ──────────────────────────────────────────────────

class TestVectorStoreInit:

    def test_raises_without_api_key(self, monkeypatch):
        """Should raise ValueError when GOOGLE_API_KEY is not set."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            VectorStore()

    def test_initializes_with_api_key(self, monkeypatch):
        """Should initialize successfully when GOOGLE_API_KEY is present."""
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
        vs = VectorStore()
        assert vs is not None

    def test_chroma_initialized_with_correct_collection(self, monkeypatch):
        """Should use 'nextleap_courses' as the ChromaDB collection name."""
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
        VectorStore()
        _, kwargs = mock_chroma_class.call_args
        assert kwargs.get("collection_name") == "nextleap_courses"

    def test_custom_persist_directory(self, monkeypatch):
        """Should pass the custom persist_directory to ChromaDB."""
        monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")
        VectorStore(persist_directory="custom/path")
        _, kwargs = mock_chroma_class.call_args
        assert kwargs.get("persist_directory") == "custom/path"


# ── Tests: add_documents ───────────────────────────────────────────────────

class TestVectorStoreAddDocuments:

    def test_add_documents_calls_chroma(self, store):
        """Should call chroma.add_documents with the provided docs."""
        docs = [MockDocument("Content A"), MockDocument("Content B")]
        store.add_documents(docs)
        mock_chroma_instance.add_documents.assert_called_once_with(documents=docs)

    def test_empty_docs_skips_chroma(self, store):
        """Should NOT call chroma.add_documents when docs list is empty."""
        store.add_documents([])
        mock_chroma_instance.add_documents.assert_not_called()

    def test_add_documents_propagates_exception(self, store):
        """Should re-raise exceptions from the underlying chroma call."""
        mock_chroma_instance.add_documents.side_effect = RuntimeError("DB error")
        with pytest.raises(RuntimeError, match="DB error"):
            store.add_documents([MockDocument("Some content")])


# ── Tests: query_similar ───────────────────────────────────────────────────

class TestVectorStoreQuerySimilar:

    def test_query_returns_results(self, store):
        """Should return whatever similarity_search provides."""
        expected = [MockDocument("Result 1"), MockDocument("Result 2")]
        mock_chroma_instance.similarity_search.return_value = expected

        result = store.query_similar("test query", k=2)
        assert result == expected

    def test_query_uses_correct_k(self, store):
        """Should pass k to similarity_search."""
        mock_chroma_instance.similarity_search.return_value = []
        store.query_similar("query", k=7)
        mock_chroma_instance.similarity_search.assert_called_once_with("query", k=7)

    def test_query_returns_empty_on_exception(self, store):
        """Should return [] instead of raising when similarity_search fails."""
        mock_chroma_instance.similarity_search.side_effect = Exception("Search error")
        result = store.query_similar("broken query")
        assert result == []

    def test_default_k_is_5(self, store):
        """Default k should be 5."""
        mock_chroma_instance.similarity_search.return_value = []
        store.query_similar("anything")
        mock_chroma_instance.similarity_search.assert_called_once_with("anything", k=5)


# ── Tests: clear ───────────────────────────────────────────────────────────

class TestVectorStoreClear:

    def test_clear_removes_directory(self, store, tmp_path, monkeypatch):
        """clear() should delete the persist directory if it exists."""
        # Create a temporary directory to simulate the store's persist dir
        persist_dir = tmp_path / "chroma_test"
        persist_dir.mkdir()
        store.persist_directory = str(persist_dir)

        store.clear()
        assert not persist_dir.exists()

    def test_clear_reinitializes_store(self, store, tmp_path):
        """clear() should reinitialize the ChromaDB store after deletion."""
        persist_dir = tmp_path / "chroma_clear_test"
        persist_dir.mkdir()
        store.persist_directory = str(persist_dir)

        initial_call_count = mock_chroma_class.call_count
        store.clear()
        # One additional call to re-init the store
        assert mock_chroma_class.call_count == initial_call_count + 1

    def test_clear_noop_when_no_directory(self, store, tmp_path):
        """clear() should not raise when the persist directory doesn't exist."""
        store.persist_directory = str(tmp_path / "nonexistent")
        # Should complete without raising
        store.clear()
