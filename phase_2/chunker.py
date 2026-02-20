import logging
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Splits long documents into smaller chunks suitable for embedding.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len,
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of documents into chunks.
        """
        if not documents:
            return []
            
        chunks = self.splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        
        # Filter out very small chunks that might be noise
        filtered_chunks = [c for c in chunks if len(c.page_content.strip()) > 10]
        if len(filtered_chunks) < len(chunks):
            logger.info(f"Filtered out {len(chunks) - len(filtered_chunks)} small chunks.")
            
        return filtered_chunks
