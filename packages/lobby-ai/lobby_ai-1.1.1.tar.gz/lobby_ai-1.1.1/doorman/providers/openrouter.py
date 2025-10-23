"""OpenRouter API provider integration."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import httpx
import tiktoken
from pydantic import BaseModel

from doorman.core.database import get_db_session


class OpenRouterConfig(BaseModel):
    """OpenRouter configuration."""

    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    app_name: str = "Doorman"
    site_url: str = "https://github.com/franco/doorman"
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "OpenRouterConfig":
        """Create config from environment variables and global config."""
        # First try environment variables
        api_key = os.getenv("OPENROUTER_API_KEY")

        # If not found in environment, try getting from global config
        if not api_key:
            try:
                from doorman.config.manager import get_config

                config = get_config()
                api_key = config.openrouter_api_key
            except Exception:
                pass  # If config manager fails, continue with None

        return cls(
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            app_name=os.getenv("DOORMAN_APP_NAME", "Doorman"),
            site_url=os.getenv("DOORMAN_SITE_URL", "https://github.com/franco/doorman"),
        )


class OpenRouterUsage(BaseModel):
    """Usage statistics from OpenRouter response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenRouterResponse(BaseModel):
    """OpenRouter API response."""

    content: str
    model: str
    usage: OpenRouterUsage
    cost_usd: Optional[float] = None
    raw_response: Dict[str, Any]


class OpenRouterProvider:
    """OpenRouter API provider with usage tracking."""

    def __init__(self, config: Optional[OpenRouterConfig] = None):
        self.config = config or OpenRouterConfig.from_env()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        if not self.config.api_key:
            raise ValueError("OpenRouter API key is required")

        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "HTTP-Referer": self.config.site_url,
            "X-Title": self.config.app_name,
            "Content-Type": "application/json",
        }

    def _estimate_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Estimate token count using tiktoken."""
        try:
            # Use appropriate encoding for the model
            if "gpt-4" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Fallback to cl100k_base for most OpenAI-compatible models
                encoding = tiktoken.get_encoding("cl100k_base")

            return len(encoding.encode(text))
        except Exception:
            # Rough fallback estimation (4 chars = 1 token)
            return len(text) // 4

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-3.5-turbo",
        user_id: Optional[UUID] = None,
        taxonomy_id: Optional[UUID] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> OpenRouterResponse:
        """Make a chat completion request."""

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        # Add user parameter for safety if user_id provided
        if user_id:
            payload["user"] = str(user_id)

        try:
            response = await self.client.post(
                f"{self.config.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            # Extract response content
            content = ""
            if data.get("choices") and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                elif "delta" in choice and "content" in choice["delta"]:
                    content = choice["delta"]["content"]

            # Extract usage statistics
            usage = OpenRouterUsage()
            if "usage" in data:
                usage_data = data["usage"]
                usage.prompt_tokens = usage_data.get("prompt_tokens", 0)
                usage.completion_tokens = usage_data.get("completion_tokens", 0)
                usage.total_tokens = usage_data.get("total_tokens", 0)

            # If no usage data, estimate tokens
            if usage.total_tokens == 0:
                prompt_text = " ".join(msg.get("content", "") for msg in messages)
                usage.prompt_tokens = self._estimate_tokens(prompt_text, model)
                usage.completion_tokens = self._estimate_tokens(content, model)
                usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

            # Extract cost if available
            cost_usd = None
            if "usage" in data and "total_cost" in data["usage"]:
                cost_usd = data["usage"]["total_cost"]

            # Record usage in database
            if user_id:
                await self._record_usage(
                    user_id=user_id,
                    model=model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    cost_usd=cost_usd,
                    taxonomy_id=taxonomy_id,
                    source="openrouter_chat",
                )

            return OpenRouterResponse(
                content=content,
                model=model,
                usage=usage,
                cost_usd=cost_usd,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            raise Exception(
                f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise Exception(f"OpenRouter request failed: {str(e)}")

    async def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002",
        user_id: Optional[UUID] = None,
    ) -> Tuple[List[List[float]], int]:
        """Generate embeddings for texts."""

        payload = {
            "model": model,
            "input": texts,
        }

        if user_id:
            payload["user"] = str(user_id)

        try:
            response = await self.client.post(
                f"{self.config.base_url}/embeddings",
                headers=self._get_headers(),
                json=payload,
            )
            response.raise_for_status()

            data = response.json()

            # Extract embeddings
            embeddings = []
            if "data" in data:
                for item in data["data"]:
                    embeddings.append(item["embedding"])

            # Extract usage
            total_tokens = 0
            if "usage" in data:
                total_tokens = data["usage"].get("total_tokens", 0)

            # Record usage
            if user_id:
                await self._record_usage(
                    user_id=user_id,
                    model=model,
                    input_tokens=total_tokens,
                    output_tokens=0,
                    source="openrouter_embedding",
                )

            return embeddings, total_tokens

        except httpx.HTTPStatusError as e:
            raise Exception(
                f"OpenRouter embedding error: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise Exception(f"OpenRouter embedding failed: {str(e)}")

    async def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter."""
        try:
            response = await self.client.get(
                f"{self.config.base_url}/models",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            return data.get("data", [])

        except Exception as e:
            raise Exception(f"Failed to get models: {str(e)}")

    async def test_connection(self) -> bool:
        """Test API connection with a minimal request."""
        try:
            await self.get_models()
            return True
        except Exception:
            return False

    async def _record_usage(
        self,
        user_id: UUID,
        model: str,
        input_tokens: int,
        output_tokens: int,
        source: str,
        taxonomy_id: Optional[UUID] = None,
        cost_usd: Optional[float] = None,
    ) -> None:
        """Record usage in the database."""
        try:
            async with get_db_session() as db:
                await db.record_usage(
                    user_id=user_id,
                    provider="openrouter",
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    source=source,
                    taxonomy_id=taxonomy_id,
                    cost_usd_estimated=cost_usd,
                )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to record usage: {e}")


class StructuredGenerator:
    """Helper for structured generation with JSON schemas."""

    def __init__(self, provider: OpenRouterProvider):
        self.provider = provider

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "openai/gpt-3.5-turbo",
        user_id: Optional[UUID] = None,
        taxonomy_id: Optional[UUID] = None,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """Generate JSON response matching the provided schema."""

        # Construct system message with schema constraint
        system_message = f"""You are a JSON generator. Respond ONLY with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Do not include any explanation or markdown formatting. Output only the JSON."""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(max_retries + 1):
            try:
                response = await self.provider.chat(
                    messages=messages,
                    model=model,
                    user_id=user_id,
                    taxonomy_id=taxonomy_id,
                    temperature=0.3,  # Lower temperature for more consistent JSON
                    max_tokens=1000,
                )

                # Parse JSON response
                json_data = json.loads(response.content.strip())

                # Basic schema validation could be added here
                return json_data

            except json.JSONDecodeError as e:
                if attempt == max_retries:
                    raise Exception(
                        f"Failed to generate valid JSON after {max_retries + 1} attempts: {e}"
                    )
                # Add error context for retry
                error_content = "Invalid JSON"
                messages.append({"role": "assistant", "content": error_content})
                messages.append(
                    {
                        "role": "user",
                        "content": "That was invalid JSON. Please provide valid JSON matching the schema exactly.",
                    }
                )
            except Exception as e:
                if attempt == max_retries:
                    raise e
                await asyncio.sleep(1)  # Brief delay before retry

        raise Exception("Unexpected error in structured generation")


# Global provider instance
_provider: Optional[OpenRouterProvider] = None


async def get_openrouter_provider() -> OpenRouterProvider:
    """Get global OpenRouter provider instance."""
    global _provider
    if _provider is None:
        _provider = OpenRouterProvider()
    return _provider


async def get_structured_generator() -> StructuredGenerator:
    """Get structured generator instance."""
    provider = await get_openrouter_provider()
    return StructuredGenerator(provider)
