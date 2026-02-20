"""
Unit tests for phase_2/chunker.py (TextChunker)

TextChunker wraps langchain's RecursiveCharacterTextSplitter.
We mock the splitter to test our own logic (empty-list guard,
small-chunk filtering) without installing langchain packages.
"""

import sys
from unittest.mock import MagicMock, patch


# ── Inject mocks before importing phase_2 ──────────────────────────────────

class MockDocument:
    """Minimal stand-in for langchain_core.documents.Document"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}

lc_core = MagicMock()
lc_core.documents.Document = MockDocument
sys.modules.setdefault("langchain_core", lc_core)
sys.modules.setdefault("langchain_core.documents", lc_core.documents)

# Mock langchain_text_splitters so we control split_documents
mock_splitter_instance = MagicMock()
mock_splitter_class = MagicMock(return_value=mock_splitter_instance)
lc_splitters = MagicMock()
lc_splitters.RecursiveCharacterTextSplitter = mock_splitter_class
sys.modules["langchain_text_splitters"] = lc_splitters

from phase_2.chunker import TextChunker  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────────

def make_doc(content: str) -> MockDocument:
    return MockDocument(page_content=content, metadata={"source": "test"})


# ── Tests ──────────────────────────────────────────────────────────────────

class TestTextChunkerEmptyInput:
    """Edge cases with empty inputs."""

    def setup_method(self):
        mock_splitter_instance.reset_mock()
        self.chunker = TextChunker()

    def test_empty_list_returns_empty(self):
        """chunk_documents([]) should return [] without calling the splitter."""
        result = self.chunker.chunk_documents([])
        assert result == []
        mock_splitter_instance.split_documents.assert_not_called()


class TestTextChunkerFiltering:
    """Tests that tiny chunks are filtered out."""

    def setup_method(self):
        mock_splitter_instance.reset_mock()
        self.chunker = TextChunker()

    def test_small_chunks_filtered(self):
        """Chunks with content ≤ 10 chars after stripping should be removed."""
        docs = [make_doc("Hello world")]
        # Simulate splitter returning one normal and one tiny chunk
        mock_splitter_instance.split_documents.return_value = [
            MockDocument(page_content="This is a valid chunk with real content."),
            MockDocument(page_content="tiny"),   # <= 10 chars — should be removed
            MockDocument(page_content="   "),    # whitespace only — should be removed
        ]

        result = self.chunker.chunk_documents(docs)
        assert len(result) == 1
        assert result[0].page_content == "This is a valid chunk with real content."

    def test_all_valid_chunks_kept(self):
        """All chunks above the size threshold should be retained."""
        docs = [make_doc("Some real content here")]
        mock_splitter_instance.split_documents.return_value = [
            MockDocument(page_content="Chunk A — longer than 10 chars."),
            MockDocument(page_content="Chunk B — also longer than 10 chars."),
        ]

        result = self.chunker.chunk_documents(docs)
        assert len(result) == 2

    def test_all_chunks_tiny_returns_empty(self):
        """If all chunks are tiny, return an empty list."""
        docs = [make_doc("Hi")]
        mock_splitter_instance.split_documents.return_value = [
            MockDocument(page_content="ok"),
            MockDocument(page_content="hi"),
        ]

        result = self.chunker.chunk_documents(docs)
        assert result == []


class TestTextChunkerPassthrough:
    """Tests that metadata is preserved through chunking."""

    def setup_method(self):
        mock_splitter_instance.reset_mock()
        self.chunker = TextChunker()

    def test_metadata_preserved(self):
        """Metadata on input documents should be carried through to chunks."""
        doc = MockDocument(
            page_content="A sufficiently long chunk to pass the filter check.",
            metadata={"section_type": "overview", "source": "https://nextleap.app"}
        )
        mock_splitter_instance.split_documents.return_value = [doc]

        result = self.chunker.chunk_documents([doc])
        assert result[0].metadata["section_type"] == "overview"
        assert result[0].metadata["source"] == "https://nextleap.app"

    def test_splitter_called_with_documents(self):
        """The underlying splitter must be called with the input documents."""
        docs = [make_doc("Content for the splitter to process.")]
        mock_splitter_instance.split_documents.return_value = docs

        self.chunker.chunk_documents(docs)
        mock_splitter_instance.split_documents.assert_called_once_with(docs)
