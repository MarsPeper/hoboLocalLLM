import logging
from typing import List
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingsManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu", api_url: str = None):
        self.model_name = model_name
        self.device = device
        self.api_url = api_url  # Optional: local llama-server endpoint
        self._model = None

    @property
    def model(self):
        if self._model is None and not self.api_url:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local SentenceTransformer model '{self.model_name}' on '{self.device}'...")
                self._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info("Model loaded successfully.")
            except ImportError:
                logger.warning("sentence-transformers package not found. Will attempt to use LLM API for embeddings.")
                if not self.api_url:
                    self.api_url = "http://localhost:8080/v1"
            except Exception as e:
                logger.error(f"Error loading local SentenceTransformer model: {e}")
                raise e
        return self._model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        # If local model is not loaded or we have api_url configured, try API first
        if self.api_url:
            try:
                logger.info(f"Generating embeddings via LLM API endpoint: {self.api_url}/embeddings")
                response = httpx.post(
                    f"{self.api_url}/embeddings",
                    json={"input": texts, "model": self.model_name},
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                # Extract embeddings in the original order (OpenAI /embeddings standard returns list of objects with an 'index')
                items = data.get("data", [])
                if items:
                    sorted_items = sorted(items, key=lambda x: x.get("index", 0))
                    return [item["embedding"] for item in sorted_items]
            except Exception as e:
                logger.error(f"LLM API embeddings call failed: {e}")
                if self._model is None:
                    # Try to load local model as a fallback
                    try:
                        from sentence_transformers import SentenceTransformer
                        self._model = SentenceTransformer(self.model_name, device=self.device)
                    except Exception as local_err:
                        raise RuntimeError("Failed both LLM API and local SentenceTransformer embedding generation.") from local_err
        
        # Local SentenceTransformer execution
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings locally: {e}")
            raise e

    def get_embedding(self, text: str) -> List[float]:
        return self.get_embeddings([text])[0]
