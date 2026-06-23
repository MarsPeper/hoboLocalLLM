import logging
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    SparseVectorParams,
    SparseIndexParams,
    Filter,
    FieldCondition,
    MatchValue
)
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore, RetrievalMode

# Import Ranker first to avoid Pydantic validation errors in langchain_community
from flashrank import Ranker
from langchain_community.document_compressors import FlashrankRerank

logger = logging.getLogger(__name__)


class VectorStore:
    """
    LangChain Qdrant Vector Store wrapper supporting:
    - Dense vector index
    - Sparse vector index (FastEmbed SPLADE/BM25)
    - Hybrid Retrieval (Dense + Sparse with Reciprocal Rank Fusion)
    - Contextual Compression & Reranking via FlashRank
    """

    def __init__(
        self,
        collection_name: str,
        dense_embeddings,
        sparse_embeddings,
        path: str = None,
        url: str = None,
        use_hybrid_search: bool = True
    ):
        self.collection_name = collection_name
        self.dense_embeddings = dense_embeddings
        self.sparse_embeddings = sparse_embeddings

        # 1. Initialize client
        if path:
            logger.info(f"Using local Qdrant storage: {path}")
            self.client = QdrantClient(path=path)
        elif url:
            logger.info(f"Connecting to Qdrant server: {url}")
            self.client = QdrantClient(url=url)
        else:
            logger.info("Using in-memory Qdrant")
            self.client = QdrantClient(":memory:")

        # 2. Ensure collection configuration (Dense + Sparse named 'sparse')
        self._ensure_collection()

        # 3. Create LangChain QdrantVectorStore
        retrieval_mode = RetrievalMode.HYBRID if use_hybrid_search else RetrievalMode.DENSE
        logger.info(f"Initializing QdrantVectorStore in {retrieval_mode.name} mode")
        
        self.store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.dense_embeddings,
            sparse_embedding=self.sparse_embeddings,
            sparse_vector_name="sparse",
            retrieval_mode=retrieval_mode
        )

    def _ensure_collection(self):
        """Ensures collection exists with both dense and sparse configurations."""
        exists = False
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collections: {e}")

        if not exists:
            # Determine dense dimensions dynamically
            try:
                dense_dim = len(self.dense_embeddings.embed_query("dummy text"))
            except Exception as e:
                logger.warning(f"Could not determine embedding dimensions: {e}. Defaulting to 384.")
                dense_dim = 384

            logger.info(
                f"Creating collection '{self.collection_name}' with dense_dim={dense_dim} and sparse support..."
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dense_dim, distance=Distance.COSINE),
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=SparseIndexParams(on_disk=True)
                    )
                }
            )
            logger.info("Collection created successfully.")

    # =================================
    # Add Documents
    # =================================

    def add_documents(self, documents: List[Document]):
        """Add LangChain Documents to the vector store (automatically embeds dense + sparse)."""
        if not documents:
            return
        logger.info(f"Adding {len(documents)} documents to Qdrant collection...")
        self.store.add_documents(documents)
        logger.info("Documents added successfully.")

    # =================================
    # Similarity Search & Reranking
    # =================================

    def search_similar(
        self,
        query: str,
        top_k: int = 4,
        use_reranker: bool = True,
        reranker_model: str = "ms-marco-MiniLM-L-12-v2",
        base_retrieve_k: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching chunks using the initialized RetrievalMode.
        If use_reranker is enabled, retrieves base_retrieve_k chunks and compresses them using FlashRank down to top_k.
        """
        k_to_fetch = base_retrieve_k if use_reranker else top_k
        logger.info(f"Searching similar for: '{query}' (fetching top {k_to_fetch} base candidates)")

        # 1. Base Retrieval (with scores)
        # LangChain's similarity_search_with_relevance_scores or similarity_search_with_score
        # Qdrant similarity_search_with_score returns List[Tuple[Document, float]]
        docs_with_scores = self.store.similarity_search_with_score(query, k=k_to_fetch)
        
        # Flatten into list of documents, storing base score in metadata
        retrieved_docs = []
        for doc, score in docs_with_scores:
            doc.metadata["base_score"] = score
            retrieved_docs.append(doc)

        # 2. Contextual Compression / Reranking
        if use_reranker and retrieved_docs:
            logger.info(f"Reranking {len(retrieved_docs)} candidates using FlashRank ({reranker_model})...")
            try:
                # Initialize FlashRank compressor
                compressor = FlashrankRerank(
                    model=reranker_model,
                    top_n=top_k
                )
                reranked_docs = compressor.compress_documents(retrieved_docs, query)
                final_docs = reranked_docs
            except Exception as e:
                logger.error(f"FlashRank reranking failed: {e}. Falling back to base ranking.")
                final_docs = retrieved_docs[:top_k]
        else:
            final_docs = retrieved_docs[:top_k]

        # 3. Format into output dicts matching front-end contract
        formatted_results = []
        for doc in final_docs:
            # Flashrank stores score in metadata['relevance_score']
            score = doc.metadata.get("relevance_score")
            if score is None:
                score = doc.metadata.get("base_score", 0.0)

            formatted_results.append({
                "content": doc.page_content,
                "file_name": doc.metadata.get("file_name", "unknown"),
                "chunk_index": doc.metadata.get("chunk_index", 0),
                "total_chunks": doc.metadata.get("total_chunks", 0),
                "score": float(score)
            })

        return formatted_results

    # =================================
    # List indexed files
    # =================================

    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """Returns unique files stored in the collection with chunk counts."""
        files = {}
        # Scroll through Qdrant collection points fetching the 'metadata' payload field
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=10000,
            with_payload=["metadata"],
            with_vectors=False
        )

        for rec in records:
            if not rec.payload:
                continue
            metadata = rec.payload.get("metadata")
            if not metadata or not isinstance(metadata, dict):
                continue
            name = metadata.get("file_name")
            if not name:
                continue
            if name not in files:
                files[name] = {
                    "file_name": name,
                    "chunk_count": 1
                }
            else:
                files[name]["chunk_count"] += 1

        return list(files.values())

    # =================================
    # Delete File Chunks
    # =================================

    def delete_file(self, file_name: str):
        """Removes all points associated with a specific file_name payload."""
        logger.info(f"Deleting chunks for file: {file_name}")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.file_name",
                        match=MatchValue(value=file_name)
                    )
                ]
            )
        )
        logger.info("Deletion complete.")

    # =================================
    # Reset Database
    # =================================

    def reset_database(self):
        """Drops the entire collection."""
        logger.warning(f"Resetting database: dropping collection '{self.collection_name}'")
        self.client.delete_collection(collection_name=self.collection_name)
        # Recreate collection to ensure it exists
        self._ensure_collection()
        logger.info("Database reset and collection recreated.")