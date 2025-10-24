"""Embedding service for pgvector MCP server."""

from typing import List

from langchain_azure_ai.embeddings import AzureAIEmbeddingsModel
from langchain_openai.embeddings import AzureOpenAIEmbeddings
import numpy as np

from ..config import get_settings
from ..exceptions import ConfigurationError, EmbeddingError

import logging

logger = logging.getLogger("embedding_service")


class EmbeddingService:
    """Service for generating text embeddings using Azure OpenAI."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._azure_openai_client = None

    def _get_client(self) -> AzureOpenAIEmbeddings:
        """Get Azure OpenAI embedding client (lazy initialization)."""
        if self._azure_openai_client is not None:
            return self._azure_openai_client

        if not self.settings.azure_openai_endpoint:
            logger.error("Azure OpenAI endpoint not configured")
            raise ConfigurationError(
                "Azure OpenAI endpoint is required but not configured. "
                "Please set AZURE_OPENAI_ENDPOINT environment variable",
                code="MISSING_API_KEY",
            )
        if not self.settings.azure_openai_api_key:
            logger.error("Azure OpenAI API key not configured")
            raise ConfigurationError(
                "Azure OpenAI API key is required but not configured. "
                "Please set AZURE_OPENAI_API_KEY environment variable",
                code="MISSING_API_KEY",
            )

        print("Initializing Azure OpenAI Embeddings client...")
        print(f"Endpoint: {self.settings.azure_openai_endpoint}")
        print(f"API Key: {self.settings.azure_openai_api_key}")
        print(f"Model: {self.settings.azure_openai_model}")

        try:
            self._azure_openai_client = AzureOpenAIEmbeddings(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                model=self.settings.azure_openai_model,
                azure_deployment=self.settings.azure_openai_model,  # Langchain uses azure_deployment for model name
                chunk_size=16,  # Default chunk size for batching
            )
            self._client = "azure_openai"
            logger.info("Azure OpenAI client initialized successfully")
            return self._azure_openai_client
        except Exception as e:
            logger.error(f"Azure OpenAI library not available or configuration error: {e}")
            raise ConfigurationError(
                "Azure OpenAI library is required and configured correctly. "
                "Please install: pip install langchain-openai and check your environment variables.",
                code="MISSING_DEPENDENCY",
            ) from e

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using Azure OpenAI."""
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            raise EmbeddingError("Cannot generate embedding for empty text", code="EMPTY_INPUT")

        try:
            client = self._get_client()
            embedding = client.embed_query(text)
            logger.debug(f"Generated embedding for single text (length: {len(text)})")
            return embedding
        except (ConfigurationError, EmbeddingError):
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in embed_text: {e}, text length: {len(text)}")
            raise EmbeddingError(f"Failed to generate embedding: {e}") from e

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Azure OpenAI."""
        if not texts:
            return []

        client = self._get_client()
        all_embeddings = []

        try:
            all_embeddings = client.embed_documents(texts)
            logger.debug(f"Generated embeddings for {len(texts)} texts.")
        except Exception as e:
            logger.error(f"Azure OpenAI batch embedding failed: {e}")
            raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e

        return all_embeddings

    def _l2_normalize_vector(self, vector: list) -> list:
        """L2 normalize vector to ensure vector length is 1, optimize cosine distance calculation"""
        # Langchain's AzureOpenAIEmbeddings typically returns L2 normalized embeddings.
        # This method is kept for explicit control if needed, but might be redundant.
        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)

        if norm == 0:
            logger.warning("Vector norm is 0, cannot perform L2 normalization")
            return vector

        normalized = vec / norm
        return normalized.tolist()

    def check_api_status(self) -> bool:
        """Check if Azure OpenAI embedding service is available."""
        client = self._get_client()
        # Attempt to embed a dummy text to verify connectivity
        client.embed_query("hello world")
