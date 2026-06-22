# Automated verification script for LocalRAG pipeline (plain text output for Windows console compatibility)
import os
import sys
import random

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import RecursiveCharacterTextSplitter
from embeddings_manager import EmbeddingsManager
from vector_store import VectorStore

def run_tests():
    print("=========================================")
    print("Running LocalRAG Backend Pipeline Tests")
    print("=========================================")
    
    # 1. Test Text Splitter
    print("\n[1/3] Testing Recursive Character Text Splitter...")
    text = "Hello world! This is a test paragraph.\n\nHere is a second paragraph that has some text to split."
    splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5)
    chunks = splitter.split_text(text)
    print(f"Generated {len(chunks)} chunks:")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i}: '{c}'")
    
    assert len(chunks) > 0, "Error: No chunks generated!"
    print("[SUCCESS] Text Splitter test passed.")
    
    # 2. Test Embeddings Manager (Local Model)
    print("\n[2/3] Testing local SentenceTransformer embedding generation...")
    try:
        manager = EmbeddingsManager(model_name="all-MiniLM-L6-v2", device="cpu")
        emb = manager.get_embedding("Hello world")
        print(f"Generated embedding dimensions: {len(emb)}")
        assert len(emb) == 384, f"Error: Expected dimension 384, got {len(emb)}"
        print("[SUCCESS] Embeddings Manager test passed.")
    except Exception as e:
        print(f"[FAIL] Embeddings Manager test failed: {e}")
        sys.exit(1)
    
    # 3. Test Vector Store Operations (In Memory)
    print("\n[3/3] Testing local Qdrant Vector Store indexing and searches...")
    try:
        store = VectorStore(collection_name="test_collection", path=None) # runs in-memory
        mock_chunks = [
            {"content": "Retrieval-Augmented Generation (RAG) is a technique.", "metadata": {"file_name": "rag_info.txt", "chunk_index": 0, "total_chunks": 2}},
            {"content": "Qdrant is a highly efficient vector database.", "metadata": {"file_name": "rag_info.txt", "chunk_index": 1, "total_chunks": 2}}
        ]
        
        # Generate real embeddings using manager
        vector1 = manager.get_embedding(mock_chunks[0]["content"])
        vector2 = manager.get_embedding(mock_chunks[1]["content"])
        mock_vectors = [vector1, vector2]
        
        # Add to collection
        store.add_chunks(mock_chunks, mock_vectors)
        print("Successfully indexed chunks.")
        
        # List files
        files = store.get_indexed_files()
        print(f"Indexed documents in DB: {files}")
        assert len(files) == 1, f"Error: Expected 1 file, got {len(files)}"
        assert files[0]["file_name"] == "rag_info.txt", f"Error: Expected file 'rag_info.txt', got '{files[0]['file_name']}'"
        
        # Query similarity search
        query_vec = manager.get_embedding("What is Qdrant?")
        results = store.search_similar(query_vec, top_k=1)
        print(f"Query: 'What is Qdrant?' -> Top Match: '{results[0]['content']}' (Score: {results[0]['score']:.4f})")
        assert "Qdrant" in results[0]["content"], "Error: Query failed to retrieve correct context!"
        
        # Delete document index
        store.delete_file("rag_info.txt")
        files_after = store.get_indexed_files()
        print(f"Indexed documents after deletion: {files_after}")
        assert len(files_after) == 0, "Error: Document index deletion failed!"
        
        print("[SUCCESS] Vector Store operations test passed.")
    except Exception as e:
        print(f"[FAIL] Vector Store test failed: {e}")
        sys.exit(1)

    print("\n=========================================")
    print("All backend pipeline tests passed!")
    print("=========================================")

if __name__ == "__main__":
    run_tests()
