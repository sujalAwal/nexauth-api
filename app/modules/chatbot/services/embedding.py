import logging
from typing import List, Optional
from openai import AsyncOpenAI
import tiktoken
from app.core.config import settings
from openai import AsyncAzureOpenAI


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using OpenAI"""
    
    def __init__(self):
        if settings.EMBEDDING_PROVIDER.lower() == "openai":
            self.client = AsyncOpenAI(
                base_url=settings.EMBEDDING_BASE_URL,
                api_key=settings.EMBEDDING_API_KEY,
            )
        elif settings.EMBEDDING_PROVIDER.lower() == "azure":
            self.client = AsyncAzureOpenAI(
                azure_endpoint=settings.EMBEDDING_BASE_URL,
                api_key=settings.EMBEDDING_API_KEY,
                api_version=settings.EMBEDDING_API_VERSION,
            )
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.tokenizer = tiktoken.get_encoding("cl100k_base")


    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions
        )
        
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        
        if batch_size is None:
            batch_size = settings.EMBEDDING_BATCH_SIZE
        
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            logger.info(f"Embedding batch {i//batch_size + 1}, size: {len(batch)}")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimensions
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
            
        
        return all_embeddings
    
    def count_tokens(self, text: str) -> int:
        """Count number of tokens in text"""
        return len(self.tokenizer.encode(text))
    
    async def embed_query(self, question: str) -> List[float]:
        """Generate embedding for a search query (same as embed_text but with logging)"""
        
        token_count = self.count_tokens(question)
        logger.info(f"Embedding query: '{question[:50]}...' ({token_count} tokens)")
        
        return await self.embed_text(question)


# Singleton
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service