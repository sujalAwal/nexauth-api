from typing import List, Dict, Optional, Union
import anthropic
from app.core.config import settings
from app.modules.chatbot.services.llm.base import BaseLLMProvider, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-haiku-20240307"  # Fast and cost-effective
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response from Claude"""
        
        # Extract system message if present
        system_msg = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)
        
        request_kwargs = {
            "model": self.model,
            "system": system_msg,
            "messages": user_messages,
        }
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        token_limit = max_completion_tokens or max_tokens
        if token_limit is not None:
            request_kwargs["max_tokens"] = token_limit
        request_kwargs.update(kwargs)
        
        # Convert to Claude format
        response = await self.client.messages.create(**request_kwargs)
        
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            provider="anthropic",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
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
        
        # Build messages in Claude format
        messages = []
        
        # Add documents as context
        if documents:
            docs_text = "\n\n".join([
                f"[Source: {doc.get('source', 'Unknown')}]\n{doc.get('text', '')}"
                for doc in documents
            ])
            system_prompt += f"\n\nRelevant documents:\n{docs_text}"
        
        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add user question
        messages.append({
            "role": "user",
            "content": user_question
        })
        
        response = await self.generate(
            messages=[{"role": "system", "content": system_prompt}] + messages,
            **kwargs
        )
        
        response.citations = self._extract_citations(response.content, documents)
        
        return response