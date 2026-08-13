import logging
from typing import List, Dict, Optional, Union
from openai import AsyncOpenAI
from app.core.config import settings
from app.modules.chatbot.services.llm.base import BaseLLMProvider, LLMResponse


logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self):
        logger.info("Initializing OpenAIProvider with model: %s", settings.OPENAI_MODEL)
        logger.info("OpenAI Base URL: %s", settings.OPENAI_BASE_URL)
        self.client = AsyncOpenAI(
            base_url=settings.OPENAI_BASE_URL,
            api_key=settings.OPENAI_API_KEY
        )
        self.model = settings.OPENAI_MODEL
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from OpenAI"""
        
        request_kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if max_completion_tokens is not None:
            request_kwargs["max_completion_tokens"] = max_completion_tokens
        elif max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        request_kwargs.update(kwargs)
        
        response = await self.client.chat.completions.create(**request_kwargs)
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            provider="openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        )
    
    async def generate_with_context(
        self,
        system_prompt: str,
        user_question: str,
        documents: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response with document context"""
        
        messages = self._build_context_prompt(
            system_prompt,
            user_question,
            documents,
            conversation_history
        )
        
        response = await self.generate(messages, **kwargs)
        response.citations = self._extract_citations(response.content, documents)
        
        return response