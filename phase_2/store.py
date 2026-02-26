import os
import logging
import shutil
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Manages the ChromaDB vector store.
    """

    def __init__(self, persist_directory: str = "data/chroma_db_v2"):
        self.persist_directory = persist_directory
        self.embedding_function = self._get_embedding_function()
        self.vector_store = self._init_vector_store()

    def _get_embedding_function(self):
        """Initializes the Google Generative AI Embedding function."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=api_key
        )

    def _init_vector_store(self):
        """Initializes the ChromaDB store."""
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name="nextleap_courses"
        )

    def add_documents(self, documents: List[Document]):
        """Adds documents to the vector store."""
        if not documents:
            logger.warning("No documents to add to vector store.")
            return

        logger.info(f"Adding {len(documents)} documents to vector store...")
        try:
            self.vector_store.add_documents(documents=documents)
            logger.info("Successfully added documents to vector store.")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def query_similar(self, query: str, k: int = 5) -> List[Document]:
        """Queries the vector store for similar documents."""
        logger.info(f"Querying vector store for: '{query}'")
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []

    def clear(self):
        """Clears the existing vector store."""
        # Try to delete the directory
        if os.path.exists(self.persist_directory):
            logger.info(f"Attempting to clear existing vector store at {self.persist_directory}")
            try:
                shutil.rmtree(self.persist_directory)
                logger.info(f"Successfully removed {self.persist_directory}")
            except PermissionError:
                logger.warning(f"Could not remove {self.persist_directory} due to PermissionError. This is common on Windows if the DB is in use.")
                logger.info("Attempting to delete collection instead...")
                try:
                    self.vector_store.delete_collection()
                    logger.info("Collection deleted.")
                except Exception as e:
                    logger.error(f"Failed to delete collection: {e}")
            except Exception as e:
                logger.error(f"Error clearing vector store: {e}")

        # Re-initialize
        self.vector_store = self._init_vector_store()
