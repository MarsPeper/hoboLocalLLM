# Automated verification script for LangChain LocalRAG backend pipeline
# Tests: text splitting, dense & sparse embeddings, hybrid retrieval, and FlashRank reranking

import os
import sys

# Ensure imports resolve from this directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from document_processor import RecursiveCharacterTextSplitter, process_document
from embeddings_manager import EmbeddingsManager
from vector_store import VectorStore


def run_tests():
    print("=========================================")
    print("Running LangChain LocalRAG Pipeline Tests")
    print("=========================================")

    # --------------------------------------------------
    # 1. Recursive Character Text Splitter
    # --------------------------------------------------
    print("\n[1/4] Testing Recursive Character Text Splitter...")

    text = (
        "Hello world! This is a test paragraph.\n\n"
        "Here is a second paragraph that has some text to split."
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5)
    chunks = splitter.split_text(text)

    print(f"Generated {len(chunks)} chunks:")
    for i, c in enumerate(chunks):
        print(f"  Chunk {i}: '{c}'")

    assert len(chunks) > 0, "Error: No chunks generated!"
    print("[SUCCESS] Text Splitter test passed.")


    # --------------------------------------------------
    # 2. EmbeddingsManager (Dense & Sparse)
    # --------------------------------------------------
    print("\n[2/4] Testing local Dense & Sparse embeddings...")

    try:
        manager = EmbeddingsManager(
            model_name="all-MiniLM-L6-v2",
            sparse_model_name="Qdrant/bm25",
            device="cpu"
        )

        dense_vec = manager.dense_embeddings.embed_query("Hello world")
        print(f"Generated dense dimensions: {len(dense_vec)}")
        assert len(dense_vec) == 384, f"Expected 384 dimensions, got {len(dense_vec)}"

        # FastEmbedSparse generates sparse embeddings; let's verify it initializes correctly
        assert manager.sparse_embeddings is not None
        print("[SUCCESS] Embeddings test passed.")

    except Exception as e:
        print(f"[FAIL] Embeddings test failed: {e}")
        sys.exit(1)


    # --------------------------------------------------
    # 3. VectorStore Ingestion & Retrieval (Hybrid & Rerank)
    # --------------------------------------------------
    print("\n[3/4] Testing Qdrant Hybrid Storage & FlashRank Reranker...")

    try:
        # Use in-memory Qdrant store
        store = VectorStore(
            collection_name="test_hybrid_collection",
            dense_embeddings=manager.dense_embeddings,
            sparse_embeddings=manager.sparse_embeddings,
            path=None,
            use_hybrid_search=True
        )

        from langchain_core.documents import Document
        mock_docs = [
            Document(
                page_content="Retrieval-Augmented Generation (RAG) is a machine learning technique.",
                metadata={"file_name": "rag_info.txt", "chunk_index": 0, "total_chunks": 2}
            ),
            Document(
                page_content="Qdrant is a highly efficient vector database supporting hybrid search.",
                metadata={"file_name": "rag_info.txt", "chunk_index": 1, "total_chunks": 2}
            )
        ]

        # Add documents
        store.add_documents(mock_docs)
        print("Successfully indexed 2 chunks into hybrid collection.")

        # List indexed files
        files = store.get_indexed_files()
        print(f"Indexed files: {files}")
        assert len(files) == 1, f"Expected 1 file, got {len(files)}"
        assert files[0]["file_name"] == "rag_info.txt"

        # Query 1: Similarity Hybrid Search (no rerank)
        print("\nTesting Hybrid Search (no reranker):")
        results = store.search_similar(
            query="What is Qdrant?",
            top_k=1,
            use_reranker=False
        )
        assert len(results) > 0, "No search results returned"
        print(f"Query: 'What is Qdrant?' -> Top Match: '{results[0]['content']}' (score={results[0]['score']:.4f})")
        assert "Qdrant" in results[0]["content"], "Incorrect retrieval result"

        # Query 2: Hybrid Search + FlashRank Reranker
        print("\nTesting Hybrid Search + FlashRank Reranker:")
        # We search with K=2, base=2 to trigger the rerank path
        results_reranked = store.search_similar(
            query="What is Qdrant?",
            top_k=1,
            use_reranker=True,
            reranker_model="ms-marco-MiniLM-L-12-v2",
            base_retrieve_k=2
        )
        assert len(results_reranked) > 0, "No reranked results returned"
        print(f"Query: 'What is Qdrant?' -> Reranked Top Match: '{results_reranked[0]['content']}' (score={results_reranked[0]['score']:.4f})")
        assert "Qdrant" in results_reranked[0]["content"], "Incorrect reranked retrieval result"

        # Delete file index
        store.delete_file("rag_info.txt")
        files_after = store.get_indexed_files()
        print(f"\nIndexed files after deletion: {files_after}")
        assert len(files_after) == 0, "Deletion failed"

        print("[SUCCESS] Vector Store and Reranker test passed.")

    except Exception as e:
        print(f"[FAIL] Vector Store and Reranker test failed: {e}")
        sys.exit(1)


    # --------------------------------------------------
    # 4. LLM Connector Verification (Mock or Local host)
    # --------------------------------------------------
    print("\n[4/4] Testing LangChain LLM Connector (contract check)...")
    try:
        from llm_connector import LLMConnector
        connector = LLMConnector(api_url="http://localhost:8080/v1", model_name="local-model")
        assert connector.api_url == "http://localhost:8080/v1"
        assert connector.model_name == "local-model"
        print("[SUCCESS] LLM Connector initialization verified.")
    except Exception as e:
        print(f"[FAIL] LLM Connector test failed: {e}")
        sys.exit(1)

    print("\n=========================================")
    print("All backend pipeline tests passed!")
    print("=========================================")


if __name__ == "__main__":
    run_tests()