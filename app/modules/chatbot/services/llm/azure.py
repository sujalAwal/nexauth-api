import logging
from typing import List, Dict, Optional, Union
from openai import AsyncAzureOpenAI
from openai import AsyncStream
from openai.types.chat import ChatCompletionChunk

from app.core.config import settings
from app.modules.chatbot.services.llm.base import BaseLLMProvider, LLMResponse


logger = logging.getLogger(__name__)


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider"""

    def __init__(self):
        logger.info("Initializing AzureOpenAIProvider with model: %s", settings.AZURE_OPENAI_MODEL)
        logger.info("Azure OpenAI endpoint: %s", settings.AZURE_OPENAI_BASE_URL)

        self.client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_BASE_URL,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        self.model = settings.AZURE_OPENAI_MODEL
        self.provider = "azure_openai"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
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
            provider="azure_openai",
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
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
        messages = self._build_context_prompt(
            system_prompt,
            user_question,
            documents,
            conversation_history,
        )

        response = await self.generate(messages, **kwargs)
        response.citations = self._extract_citations(response.content, documents)
        return response

    async def stream_with_context(
        self,
        system_prompt: str,
        user_question: str,
        documents: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
    ):
        """Stream a response from Azure OpenAI, yielding content tokens."""
        messages = self._build_context_prompt(
            system_prompt,
            user_question,
            documents,
            conversation_history,
        )

        request_kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if max_completion_tokens is not None:
            request_kwargs["max_completion_tokens"] = max_completion_tokens
        elif max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens

        stream: AsyncStream[ChatCompletionChunk] = await self.client.chat.completions.create(
            **request_kwargs
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

        await stream.close()