import os
import logging
import argparse
from dotenv import load_dotenv

from phase_2.processor import DataProcessor
from phase_2.chunker import TextChunker
from phase_2.store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not found in environment variables.")
        return

    parser = argparse.ArgumentParser(description="Embed Course Data")
    parser.add_argument("--data-file", default="data/raw/course_data_v2.json", help="Path to the scraped JSON data file")
    parser.add_argument("--reset-db", action="store_true", help="Clear existing vector store before adding new data")
    args = parser.parse_args()

    data_file = args.data_file
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        return

    # 1. Initialize Components
    processor = DataProcessor()
    chunker = TextChunker()
    
    try:
        store = VectorStore()
    except Exception as e:
        logger.error(f"Failed to initialize VectorStore: {e}")
        return

    # 2. Reset DB if requested
    if args.reset_db:
        store.clear()

    # 3. Load and Process Data
    logger.info("Step 1: Loading Data...")
    try:
        raw_data = processor.load_data(data_file)
    except Exception:
        return

    logger.info("Step 2: Processing Data into Documents...")
    documents = processor.process_course(raw_data)
    logger.info(f"Generated {len(documents)} initial documents.")

    # 4. Chunk Data
    logger.info("Step 3: Chunking Documents...")
    chunks = chunker.chunk_documents(documents)
    
    # 5. Store Embeddings
    logger.info("Step 4: Storing Embeddings...")
    if chunks:
        store.add_documents(chunks)
        logger.info("Done!")
    else:
        logger.warning("No chunks to store.")

if __name__ == "__main__":
    main()
