import logging
import tiktoken
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider"""
    content: str
    model: str
    provider: str
    usage: Dict
    citations: List[str] = None
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []


@dataclass
class LLMMessage:
    """Standard message format"""
    role: str  # system, user, assistant
    content: str


class ContextBuilder:
    """Build a token-budgeted prompt so we never overflow the model context window.

    Documents are assumed to be sorted by relevance (highest similarity first);
    the tail is dropped when the budget is exceeded. Conversation history is
    trimmed from oldest to newest.
    """

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        reserve_tokens: Optional[int] = None,
        limit_history_messages: Optional[int] = None,
    ):
        self.max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS
        self.reserve_tokens = reserve_tokens or settings.CONTEXT_RESERVE_TOKENS
        self.limit_history = limit_history_messages or settings.CONTEXT_HISTORY_MESSAGES
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def _count(self, text: str) -> int:
        return len(self.tokenizer.encode(text or ""))

    def build(
        self,
        system_prompt: str,
        user_question: str,
        documents: Optional[List[Dict]] = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Tuple[List[Dict[str, str]], bool]:
        """Return (messages, truncated)."""
        documents = documents or []
        history = list(conversation_history or [])[: self.limit_history]

        budget = self.max_tokens - self.reserve_tokens
        budget -= self._count(system_prompt)
        budget -= self._count(user_question)
        truncated = False

        # Documents (drop tail until it fits; sorted by relevance already)
        kept_docs: List[Dict] = []
        for doc in documents:
            rendered = f"[Source: {doc.get('source', 'Unknown')}]\n{doc.get('text', '')}"
            cost = self._count(f"Relevant documents:\n\n{rendered}") + 8
            if cost > budget and kept_docs:
                truncated = True
                break
            if cost > budget:
                truncated = True
                continue
            budget -= cost
            kept_docs.append(rendered)
        if len(kept_docs) < len(documents):
            truncated = True

        # History (keep the most recent that fits)
        kept_history: List[Dict] = []
        for msg in reversed(history):
            cost = self._count(msg.get("content", ""))
            if cost > budget:
                truncated = True
                break
            budget -= cost
            kept_history.insert(0, msg)

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if kept_docs:
            messages.append({
                "role": "system",
                "content": "Relevant documents:\n\n" + "\n\n".join(kept_docs),
            })
        messages.extend(kept_history)
        messages.append({"role": "user", "content": user_question})

        return messages, truncated


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    @property
    def context_builder(self) -> ContextBuilder:
        if not hasattr(self, "_context_builder") or self._context_builder is None:
            self._context_builder = ContextBuilder()
        return self._context_builder

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def generate_with_context(
        self,
        system_prompt: str,
        user_question: str,
        documents: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response with document context"""
        pass

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
        """Stream a response with document context.

        Default implementation words: performs a non-streaming generation and
        yields the whole content at once, so providers that do not implement
        native streaming still work. Providers should override for true tokens.
        """
        response = await self.generate_with_context(
            system_prompt=system_prompt,
            user_question=user_question,
            documents=documents,
            conversation_history=conversation_history,
            temperature=temperature,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
        )
        yield response

    def _build_context_prompt(
        self,
        system_prompt: str,
        user_question: str,
        documents: List[Dict],
        conversation_history: Optional[List[Dict]] = None,
    ) -> List[Dict[str, str]]:
        """Build a token-budgeted message list (docs + trimmed history)."""
        messages, truncated = self.context_builder.build(
            system_prompt=system_prompt,
            user_question=user_question,
            documents=documents or [],
            conversation_history=conversation_history or [],
        )
        if truncated:
            logger.warning("Context truncated to fit token budget (%s tokens).", settings.MAX_CONTEXT_TOKENS)
        return messages
    
    def _extract_citations(self, content: str, documents: List[Dict]) -> List[str]:
        """Extract source citations from documents used"""
        citations = []
        for doc in documents:
            source = doc.get('source', '')
            if source and source not in citations:
                citations.append(source)
        return citations