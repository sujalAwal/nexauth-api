import logging
from typing import Optional

from app.core.config import settings
from app.modules.chatbot.services.llm.azure import AzureOpenAIProvider
from app.modules.chatbot.services.llm.base import BaseLLMProvider, LLMResponse
from app.modules.chatbot.services.llm.claude import ClaudeProvider
from app.modules.chatbot.services.llm.deepseek import DeepSeekProvider
from app.modules.chatbot.services.llm.openai import OpenAIProvider


logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service with automatic fallback.
    Tries primary provider first, falls back to secondary on failure.
    """
    
    def __init__(self):
        self.providers = {}
        self._init_providers()
        
        # Set primary and fallback
        self.primary = self.providers.get(settings.PRIMARY_LLM)
        self.fallback = self.providers.get("openai")  # Default fallback
        
        if not self.primary:
            logger.warning(f"Primary provider '{settings.PRIMARY_LLM}' not configured. Using first available.")
            self.primary = next(iter(self.providers.values()), None)
    
    def _init_providers(self):
        """Initialize available providers"""
        
        if settings.DEEPSEEK_API_KEY:
            try:
                self.providers["deepseek"] = DeepSeekProvider()
                logger.info("✅ DeepSeek provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize DeepSeek: {e}")
        
        if settings.OPENAI_API_KEY:
            try:
                self.providers["openai"] = OpenAIProvider()
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {e}")

        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_BASE_URL and settings.AZURE_OPENAI_MODEL:
            try:
                self.providers["azure_openai"] = AzureOpenAIProvider()
                logger.info("✅ Azure OpenAI provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI: {e}")
        
        if settings.ANTHROPIC_API_KEY:
            try:
                self.providers["claude"] = ClaudeProvider()
                logger.info("✅ Claude provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Claude: {e}")
        
        if not self.providers:
            raise ValueError("No LLM providers configured. Set at least one API key.")
    
    async def generate(
        self,
        system_prompt: str,
        user_question: str,
        documents: list = None,
        conversation_history: list = None,
        use_fallback: bool = True,
        **kwargs
    ):
        """
        Generate response with automatic fallback.
        
        Args:
            system_prompt: System instructions
            user_question: User's question
            documents: Retrieved document chunks
            conversation_history: Previous messages
            use_fallback: Whether to fallback on failure
        """
        
        if documents is None:
            documents = []
        
        # Try primary provider
        try:
            response = await self.primary.generate_with_context(
                system_prompt=system_prompt,
                user_question=user_question,
                documents=documents,
                conversation_history=conversation_history,
                **kwargs
            )
            logger.info(f"✅ Generated response with {response.provider}/{response.model}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Primary provider failed: {e}")
            
            # Try fallback
            if use_fallback and self.fallback and self.fallback != self.primary:
                try:
                    logger.info(f"🔄 Falling back to {self.fallback.model}")
                    response = await self.fallback.generate_with_context(
                        system_prompt=system_prompt,
                        user_question=user_question,
                        documents=documents,
                        conversation_history=conversation_history,
                        **kwargs
                    )
                    logger.info(f"✅ Generated response with fallback {response.provider}")
                    return response
                    
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {fallback_error}")
            
            # Both failed
            raise Exception(f"All LLM providers failed. Primary: {e}")
    
    async def stream(
        self,
        system_prompt: str,
        user_question: str,
        documents: list = None,
        conversation_history: list = None,
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ):
        """
        Stream a response from the primary provider (with non-streaming
        fallback if the provider does not implement native streaming).
        Yields (content_chunk_or_full, provider, model).
        """
        if documents is None:
            documents = []
        
        provider = self.primary
        if provider is None:
            raise Exception("No LLM providers configured.")
        
        try:
            async for item in provider.stream_with_context(
                system_prompt=system_prompt,
                user_question=user_question,
                documents=documents,
                conversation_history=conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                if isinstance(item, LLMResponse):
                    yield item.content, item.provider, item.model
                else:
                    # Native streaming token
                    prov_name = getattr(provider, "provider", None) or provider.model
                    yield item, prov_name, provider.model
        except Exception as e:
            logger.error(f"Streaming failed on {provider.model}: {e}")
            # Fallback to full response via generate
            response = await provider.generate_with_context(
                system_prompt=system_prompt,
                user_question=user_question,
                documents=documents,
                conversation_history=conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            yield response.content, response.provider, response.model


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    
    if _llm_service is None:
        _llm_service = LLMService()
    
    return _llm_service