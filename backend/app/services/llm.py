from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List, Dict, Any
from dataclasses import dataclass
import httpx
import ollama
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from app.core.config import settings
import structlog

logger = structlog.get_logger()


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: Optional[int] = None
    provider: str = ""


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        pass


class OllamaProvider(BaseLLMProvider):
    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        try:
            ollama_messages = []
            if system_prompt:
                ollama_messages.append({"role": "system", "content": system_prompt})
            ollama_messages.extend(messages)

            response = await self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={"temperature": temperature, "num_predict": max_tokens},
                stream=stream,
            )

            if stream:
                return LLMResponse(content="", model=self.model, provider="ollama")

            content = response.get("message", {}).get("content", "")
            tokens = response.get("eval_count", 0) + response.get("prompt_eval_count", 0)
            return LLMResponse(content=content, model=self.model, tokens_used=tokens, provider="ollama")
        except Exception as e:
            logger.error("ollama_generate_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        ollama_messages.extend(messages)

        try:
            stream = await self.client.chat(
                model=self.model,
                messages=ollama_messages,
                options={"temperature": temperature, "num_predict": max_tokens},
                stream=True,
            )
            async for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        except Exception as e:
            logger.error("ollama_stream_error", error=str(e))
            raise


class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLOUD_MODEL

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        try:
            anthropic_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                system=system_prompt or "",
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )

            if stream:
                return LLMResponse(content="", model=self.model, provider="anthropic")

            content = "".join(block.text for block in response.content if hasattr(block, "text"))
            tokens = response.usage.input_tokens + response.usage.output_tokens
            return LLMResponse(content=content, model=self.model, tokens_used=tokens, provider="anthropic")
        except Exception as e:
            logger.error("anthropic_generate_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        anthropic_messages = [{"role": m["role"], "content": m["content"]} for m in messages]

        try:
            stream = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                system=system_prompt or "",
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.type == "content_block_delta" and hasattr(chunk.delta, "text"):
                    yield chunk.delta.text
        except Exception as e:
            logger.error("anthropic_stream_error", error=str(e))
            raise


class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.CLOUD_MODEL

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> LLMResponse:
        try:
            openai_messages = []
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            openai_messages.extend(messages)

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )

            if stream:
                return LLMResponse(content="", model=self.model, provider="openai")

            content = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0
            return LLMResponse(content=content, model=self.model, tokens_used=tokens, provider="openai")
        except Exception as e:
            logger.error("openai_generate_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})
        openai_messages.extend(messages)

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise


def get_llm_provider(provider: str = None) -> BaseLLMProvider:
    provider = provider or settings.LLM_PROVIDER

    if provider == "ollama":
        return OllamaProvider()
    elif provider == "anthropic":
        return AnthropicProvider()
    elif provider == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")