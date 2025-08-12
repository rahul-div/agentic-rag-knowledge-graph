"""
Document embedding generation for vector search using Google Gemini via Graphiti.
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from dotenv import load_dotenv
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig

from .chunker import DocumentChunk

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Gemini embedder via Graphiti
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY must be set")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embedding-001")

# Create embedder instance
gemini_embedder = GeminiEmbedder(
    config=GeminiEmbedderConfig(api_key=api_key, embedding_model=EMBEDDING_MODEL)
)


class EmbeddingGenerator:
    """Generates embeddings for document chunks."""

    def __init__(
        self,
        model: str = EMBEDDING_MODEL,
        batch_size: int = 100,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize embedding generator.

        Args:
            model: Embedding model to use (Gemini embedding-001 for our setup)
            batch_size: Number of texts to process in parallel
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.model = model
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Model-specific configurations (Gemini only)
        self.model_configs = {
            # Gemini models
            "embedding-001": {"dimensions": 768, "max_tokens": 8192},
            "text-embedding-004": {"dimensions": 768, "max_tokens": 8192},
        }

        # Default to Gemini configuration if model unknown
        if model not in self.model_configs:
            logger.warning(
                f"Unknown model {model}, using Gemini default config (768 dimensions)"
            )
            self.config = {"dimensions": 768, "max_tokens": 8192}
        else:
            self.config = self.model_configs[model]

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Gemini via Graphiti.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Truncate text if too long
        if len(text) > self.config["max_tokens"] * 4:  # Rough token estimation
            text = text[: self.config["max_tokens"] * 4]

        for attempt in range(self.max_retries):
            try:
                # Use Graphiti's GeminiEmbedder
                embedding = await gemini_embedder.create(text)

                if embedding:
                    return embedding
                else:
                    raise ValueError("No embedding returned from Gemini API")

            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "quota" in error_msg:
                    if attempt == self.max_retries - 1:
                        raise

                    # Exponential backoff for rate limits
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s")
                    await asyncio.sleep(delay)

                elif "api" in error_msg:
                    logger.error(f"API error: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Unexpected error generating embedding: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(self.retry_delay)

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts using Gemini via Graphiti.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Filter and truncate texts
        processed_texts = []
        for text in texts:
            if not text or not text.strip():
                processed_texts.append("")
                continue

            # Truncate if too long
            if len(text) > self.config["max_tokens"] * 4:
                text = text[: self.config["max_tokens"] * 4]

            processed_texts.append(text)

        for attempt in range(self.max_retries):
            try:
                # Filter out empty texts for the API call
                non_empty_texts = [
                    text for text in processed_texts if text and text.strip()
                ]

                if not non_empty_texts:
                    # Return zero vectors for all empty texts
                    return [[0.0] * self.config["dimensions"]] * len(processed_texts)

                # Use Graphiti's GeminiEmbedder for batch processing
                embeddings = await gemini_embedder.create_batch(non_empty_texts)

                # Map embeddings back to original text positions
                result_embeddings = []
                embedding_idx = 0

                for text in processed_texts:
                    if not text or not text.strip():
                        # Zero vector for empty text
                        result_embeddings.append([0.0] * self.config["dimensions"])
                    else:
                        if embedding_idx < len(embeddings):
                            result_embeddings.append(embeddings[embedding_idx])
                            embedding_idx += 1
                        else:
                            # Fallback zero vector
                            result_embeddings.append([0.0] * self.config["dimensions"])

                return result_embeddings

            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "quota" in error_msg:
                    if attempt == self.max_retries - 1:
                        raise

                    delay = self.retry_delay * (2**attempt)
                    logger.warning(f"Rate limit hit, retrying batch in {delay}s")
                    await asyncio.sleep(delay)

                elif "api" in error_msg:
                    logger.error(f"Embedding API error in batch: {e}")
                    if attempt == self.max_retries - 1:
                        # Fallback to individual processing
                        return await self._process_individually(processed_texts)
                    await asyncio.sleep(self.retry_delay)

                else:
                    logger.error(f"Unexpected error in batch embedding: {e}")
                    if attempt == self.max_retries - 1:
                        return await self._process_individually(processed_texts)
                    await asyncio.sleep(self.retry_delay)

    async def _process_individually(self, texts: List[str]) -> List[List[float]]:
        """
        Process texts individually as fallback.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            try:
                if not text or not text.strip():
                    embeddings.append([0.0] * self.config["dimensions"])
                    continue

                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)

                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Failed to embed text: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * self.config["dimensions"])

        return embeddings

    async def embed_chunks(
        self, chunks: List[DocumentChunk], progress_callback: Optional[callable] = None
    ) -> List[DocumentChunk]:
        """
        Generate embeddings for document chunks.

        Args:
            chunks: List of document chunks
            progress_callback: Optional callback for progress updates

        Returns:
            Chunks with embeddings added
        """
        if not chunks:
            return chunks

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Process chunks in batches
        embedded_chunks = []
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size

        for i in range(0, len(chunks), self.batch_size):
            batch_chunks = chunks[i : i + self.batch_size]
            batch_texts = [chunk.content for chunk in batch_chunks]

            try:
                # Generate embeddings for this batch
                embeddings = await self.generate_embeddings_batch(batch_texts)

                # Add embeddings to chunks
                for chunk, embedding in zip(batch_chunks, embeddings):
                    # Create a new chunk with embedding
                    embedded_chunk = DocumentChunk(
                        content=chunk.content,
                        index=chunk.index,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        metadata={
                            **chunk.metadata,
                            "embedding_model": self.model,
                            "embedding_dimensions": len(embedding),
                            "embedding_generated_at": datetime.now().isoformat(),
                        },
                        token_count=chunk.token_count,
                    )

                    # Add embedding as a separate attribute
                    embedded_chunk.embedding = embedding
                    embedded_chunks.append(embedded_chunk)

                # Progress update
                current_batch = (i // self.batch_size) + 1
                if progress_callback:
                    progress_callback(current_batch, total_batches)

                logger.info(f"Processed batch {current_batch}/{total_batches}")

            except Exception as e:
                logger.error(f"Failed to process batch {i // self.batch_size + 1}: {e}")

                # Add chunks without embeddings as fallback
                for chunk in batch_chunks:
                    chunk.metadata.update(
                        {
                            "embedding_error": str(e),
                            "embedding_generated_at": datetime.now().isoformat(),
                        }
                    )
                    chunk.embedding = [0.0] * self.config["dimensions"]
                    embedded_chunks.append(chunk)

        logger.info(
            f"Generated embeddings for {len(embedded_chunks)} chunks (model: {self.model}, dimensions: {self.config['dimensions']})"
        )
        return embedded_chunks

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query

        Returns:
            Query embedding
        """
        return await self.generate_embedding(query)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for this model."""
        return self.config["dimensions"]


# Cache for embeddings
class EmbeddingCache:
    """Simple in-memory cache for embeddings."""

    def __init__(self, max_size: int = 1000):
        """Initialize cache."""
        self.cache: Dict[str, List[float]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.max_size = max_size

    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        text_hash = self._hash_text(text)
        if text_hash in self.cache:
            self.access_times[text_hash] = datetime.now()
            return self.cache[text_hash]
        return None

    def put(self, text: str, embedding: List[float]):
        """Store embedding in cache."""
        text_hash = self._hash_text(text)

        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[text_hash] = embedding
        self.access_times[text_hash] = datetime.now()

    def _hash_text(self, text: str) -> str:
        """Generate hash for text."""
        import hashlib

        return hashlib.md5(text.encode()).hexdigest()


# Factory function
def create_embedder(
    model: str = EMBEDDING_MODEL, use_cache: bool = True, **kwargs
) -> EmbeddingGenerator:
    """
    Create embedding generator with optional caching.

    Args:
        model: Embedding model to use
        use_cache: Whether to use caching
        **kwargs: Additional arguments for EmbeddingGenerator

    Returns:
        EmbeddingGenerator instance
    """
    embedder = EmbeddingGenerator(model=model, **kwargs)

    if use_cache:
        # Add caching capability
        cache = EmbeddingCache()
        original_generate = embedder.generate_embedding

        async def cached_generate(text: str) -> List[float]:
            cached = cache.get(text)
            if cached is not None:
                return cached

            embedding = await original_generate(text)
            cache.put(text, embedding)
            return embedding

        embedder.generate_embedding = cached_generate

    return embedder


# Example usage
async def main():
    """Example usage of the embedder."""
    from .chunker import ChunkingConfig, create_chunker

    # Create chunker and embedder
    config = ChunkingConfig(chunk_size=200, use_semantic_splitting=False)
    chunker = create_chunker(config)
    embedder = create_embedder()

    sample_text = """
    Google's AI initiatives include advanced language models, computer vision,
    and machine learning research. The company has invested heavily in
    transformer architectures and neural network optimization.
    
    Microsoft's partnership with OpenAI has led to integration of GPT models
    into various products and services, making AI accessible to enterprise
    customers through Azure cloud services.
    """

    # Chunk the document
    chunks = chunker.chunk_document(
        content=sample_text, title="AI Initiatives", source="example.md"
    )

    print(f"Created {len(chunks)} chunks")

    # Generate embeddings
    def progress_callback(current, total):
        print(f"Processing batch {current}/{total}")

    embedded_chunks = await embedder.embed_chunks(chunks, progress_callback)

    for i, chunk in enumerate(embedded_chunks):
        print(
            f"Chunk {i}: {len(chunk.content)} chars, embedding dim: {len(chunk.embedding)}"
        )

    # Test query embedding
    query_embedding = await embedder.embed_query("Google AI research")
    print(f"Query embedding dimension: {len(query_embedding)}")


if __name__ == "__main__":
    asyncio.run(main())
