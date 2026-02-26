
import os
import logging
from dotenv import load_dotenv
from phase_2.store import VectorStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_retrieval():
    # Load environment variables
    load_dotenv()
    
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        return

    try:
        store = VectorStore()
        query = "Who are the mentors for the Product Management course?"
        logger.info(f"Running verification query: '{query}'")
        
        results = store.query_similar(query, k=3)
        
        if results:
            logger.info(f"Found {len(results)} relevant documents:")
            for i, doc in enumerate(results):
                logger.info(f"\nResult {i+1}:")
                logger.info(f"Content: {doc.page_content[:200]}...")
                logger.info(f"Metadata: {doc.metadata}")
            print("\nVerification SUCCESS: Retrieved relevant documents.")
        else:
            logger.warning("Verification FAILED: No documents retrieved.")
            
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")

if __name__ == "__main__":
    verify_retrieval()
