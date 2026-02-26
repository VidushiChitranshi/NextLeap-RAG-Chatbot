import os
from dotenv import load_dotenv
from phase_2.store import VectorStore

load_dotenv()

def debug_store():
    print("Initializing VectorStore...")
    try:
        store = VectorStore()
        # Chroma doesn't have an easy 'count' in LangChain wrapper sometimes, 
        # but we can try to query it with a very common term.
        print("Querying for 'NextLeap'...")
        results = store.query_similar("NextLeap", k=1)
        if results:
            print(f"✅ Found {len(results)} result(s).")
            print(f"Content snippet: {results[0].page_content[:200]}...")
        else:
            print("❌ No results found. The store might be empty.")
            
        # Try to access the underlying collection to get a count
        try:
            count = store.vector_store._collection.count()
            print(f"Total chunks in collection: {count}")
        except Exception as e:
            print(f"Could not get count: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_store()
