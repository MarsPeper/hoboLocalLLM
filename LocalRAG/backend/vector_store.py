import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter, FieldCondition, MatchValue

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, collection_name: str, path: str = None, url: str = None):
        self.collection_name = collection_name
        self.path = path
        self.url = url
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initializes the Qdrant Client. Prefers local disk path if specified, otherwise uses url."""
        if self.path:
            logger.info(f"Connecting to local Qdrant database stored at '{self.path}'...")
            self.client = QdrantClient(path=self.path)
        elif self.url:
            logger.info(f"Connecting to Qdrant server at '{self.url}'...")
            self.client = QdrantClient(url=self.url)
        else:
            logger.info("No storage path or URL specified. Initializing Qdrant in-memory client...")
            self.client = QdrantClient(":memory:")

    def ensure_collection(self, vector_size: int):
        """Ensures that the collection exists in Qdrant with the specified vector dimension."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            logger.info(f"Collection '{self.collection_name}' not found. Creating collection with vector size {vector_size}...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            logger.info("Collection created successfully.")
        else:
            logger.info(f"Collection '{self.collection_name}' already exists.")

    def add_chunks(self, chunks: List[Dict[str, Any]], vectors: List[List[float]]):
        """Inserts text chunks and their embeddings into the collection."""
        if not chunks or not vectors:
            return

        if len(chunks) != len(vectors):
            raise ValueError("The number of chunks must match the number of vectors.")

        vector_size = len(vectors[0])
        self.ensure_collection(vector_size)

        points = []
        for idx, chunk in enumerate(chunks):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vectors[idx],
                    payload={
                        "content": chunk["content"],
                        "file_name": chunk["metadata"]["file_name"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                        "total_chunks": chunk["metadata"]["total_chunks"]
                    }
                )
            )
            
        logger.info(f"Upserting {len(points)} chunks into collection '{self.collection_name}'...")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info("Upsert completed successfully.")

    def search_similar(self, query_vector: List[float], top_k: int = 4) -> List[Dict[str, Any]]:
        """Finds the top_k most similar document chunks for a given query vector."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            logger.warning(f"Search collection '{self.collection_name}' does not exist.")
            return []

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k
        )
        search_results = response.points

        results = []
        for res in search_results:
            results.append({
                "content": res.payload.get("content", ""),
                "file_name": res.payload.get("file_name", ""),
                "chunk_index": res.payload.get("chunk_index", 0),
                "total_chunks": res.payload.get("total_chunks", 0),
                "score": res.score
            })
        return results

    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """Retrieves a list of unique files that have been indexed in the database, with chunk counts."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            return []

        # Scroll to retrieve payload from all documents (up to 10k limits for small local setup)
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            limit=10000,
            with_payload=["file_name"],
            with_vectors=False
        )

        file_info = {}
        for rec in records:
            if rec.payload and "file_name" in rec.payload:
                fname = rec.payload["file_name"]
                if fname in file_info:
                    file_info[fname]["chunk_count"] += 1
                else:
                    file_info[fname] = {
                        "file_name": fname,
                        "chunk_count": 1
                    }

        return list(file_info.values())

    def delete_file(self, file_name: str):
        """Deletes all chunks associated with a specific file name."""
        logger.info(f"Deleting chunks for file '{file_name}' from collection '{self.collection_name}'...")
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="file_name",
                        match=MatchValue(value=file_name)
                    )
                ]
            )
        )
        logger.info("Deletion completed.")

    def reset_database(self):
        """Clears the collection completely."""
        logger.info(f"Resetting database by deleting collection '{self.collection_name}'...")
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if exists:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info("Collection deleted.")
        else:
            logger.info("Collection did not exist.")
