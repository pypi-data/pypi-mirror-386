"""
Simple OpenRouter client for CLI usage
"""

import json
import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Simple OpenRouter API client for CLI usage."""

    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://doorman.dev",
            "X-Title": "Doorman AI Orchestration",
        }

    async def generate_structured_response(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> Dict[str, Any]:
        """Generate a response using OpenRouter API."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Making OpenRouter API call to {model}")
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )

                response.raise_for_status()
                data = response.json()

                # Extract content from response
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                logger.info(
                    f"API call successful - {usage.get('total_tokens', 0)} tokens used"
                )

                return {
                    "content": content,
                    "usage": usage,
                    "model": data.get("model", model),
                    "finish_reason": data["choices"][0].get("finish_reason"),
                }

            except httpx.HTTPStatusError as e:
                error_text = e.response.text
                logger.error(
                    f"OpenRouter API error: {e.response.status_code} - {error_text}"
                )

                try:
                    error_data = json.loads(error_text)
                    error_message = error_data.get("error", {}).get("message", str(e))
                except:
                    error_message = f"HTTP {e.response.status_code}: {error_text}"

                raise Exception(f"OpenRouter API error: {error_message}")

            except httpx.TimeoutException:
                logger.error("OpenRouter API timeout")
                raise Exception("API request timed out after 30 seconds")

            except Exception as e:
                logger.error(f"OpenRouter client error: {e}")
                raise Exception(f"API client error: {str(e)}")
