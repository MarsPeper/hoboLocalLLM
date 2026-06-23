import logging
from typing import List
import httpx
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse

logger = logging.getLogger(__name__)


class LocalApiEmbeddings(Embeddings):
    """
    Fallback LangChain Embeddings class that generates embeddings using a local
    OpenAI-compatible server endpoint (e.g. llama-server's /v1/embeddings).
    """

    def __init__(self, api_url: str, model_name: str):
        self.api_url = api_url.rstrip("/") + "/embeddings"
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            logger.info(f"Generating embeddings via API: {self.api_url}")
            response = httpx.post(
                self.api_url,
                json={"input": texts, "model": self.model_name},
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            # Ensure order is preserved by sorting on 'index' if returned
            items = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in items]
        except Exception as e:
            logger.error(f"Fallback API embedding generation failed: {e}")
            raise RuntimeError(f"Fallback API embedding failed: {e}")

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


class EmbeddingsManager:
    """
    Manages both dense and sparse embeddings using LangChain and FastEmbed.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        sparse_model_name: str = "Qdrant/bm25",
        device: str = "cpu",
        api_url: str = None
    ):
        self.model_name = model_name
        self.sparse_model_name = sparse_model_name
        self.device = device
        self.api_url = api_url  # e.g., "http://localhost:8080/v1"
        self._dense_embeddings = None
        self._sparse_embeddings = None

    @property
    def dense_embeddings(self) -> Embeddings:
        """Returns the dense embedding model instance (loads lazily)."""
        if self._dense_embeddings is None:
            try:
                logger.info(f"Initializing local HuggingFaceEmbeddings with model: {self.model_name}")
                self._dense_embeddings = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={"device": self.device}
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load local HuggingFaceEmbeddings: {e}. "
                    f"Attempting fallback to LLM API endpoint..."
                )
                if self.api_url:
                    self._dense_embeddings = LocalApiEmbeddings(
                        api_url=self.api_url,
                        model_name=self.model_name
                    )
                else:
                    raise RuntimeError(
                        f"Cannot load dense embeddings. Local model failed and no api_url is configured. Details: {e}"
                    )
        return self._dense_embeddings

    @property
    def sparse_embeddings(self) -> FastEmbedSparse:
        """Returns the sparse embedding model instance (loads lazily)."""
        if self._sparse_embeddings is None:
            logger.info(f"Initializing FastEmbedSparse with model: {self.sparse_model_name}")
            self._sparse_embeddings = FastEmbedSparse(
                model_name=self.sparse_model_name
            )
        return self._sparse_embeddings