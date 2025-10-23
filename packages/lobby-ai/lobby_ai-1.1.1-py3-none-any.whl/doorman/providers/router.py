"""Smart provider routing engine with cost optimization and config inheritance."""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config.manager import get_config


class ProviderType(Enum):
    """Available AI providers."""

    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class TaskType(Enum):
    """Task categories for optimized routing."""

    CODING = "coding"
    WRITING = "writing"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    REASONING = "reasoning"


@dataclass
class ProviderCost:
    """Cost structure for a provider."""

    input_cost_per_1k: float  # USD per 1K input tokens
    output_cost_per_1k: float  # USD per 1K output tokens
    speed_score: float  # 1-10, higher is faster
    capability_score: Dict[TaskType, float]  # 1-10 per task type


@dataclass
class ProviderConfig:
    """Configuration for a specific provider."""

    provider_type: ProviderType
    api_key: Optional[str]
    base_url: str
    models: List[str]
    cost_data: ProviderCost
    enabled: bool = True


class ConfigInheritanceManager:
    """Inherits configuration from existing CLI tools."""

    def __init__(self):
        self.home = Path.home()

    def discover_existing_configs(self) -> Dict[ProviderType, Dict[str, Any]]:
        """Discover existing CLI configurations."""
        configs = {}

        # Claude CLI config
        claude_config = self._load_claude_config()
        if claude_config:
            configs[ProviderType.ANTHROPIC] = claude_config

        # Gemini CLI config
        gemini_config = self._load_gemini_config()
        if gemini_config:
            configs[ProviderType.GEMINI] = gemini_config

        # OpenRouter from env
        openrouter_config = self._load_openrouter_config()
        if openrouter_config:
            configs[ProviderType.OPENROUTER] = openrouter_config

        # OpenAI from various locations
        openai_config = self._load_openai_config()
        if openai_config:
            configs[ProviderType.OPENAI] = openai_config

        return configs

    def _load_claude_config(self) -> Optional[Dict[str, Any]]:
        """Load Claude CLI configuration."""
        possible_paths = [
            self.home / ".config" / "claude" / "config.json",
            self.home / ".claude" / "config.json",
            self.home / ".anthropic",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        if path.suffix == ".json":
                            config = json.load(f)
                        else:
                            # Handle simple key files
                            config = {"api_key": f.read().strip()}

                        return {
                            "api_key": config.get("api_key")
                            or os.getenv("ANTHROPIC_API_KEY"),
                            "model": config.get("model", "claude-3-sonnet-20240229"),
                            "source": str(path),
                        }
                except Exception:
                    continue

        # Check environment
        if os.getenv("ANTHROPIC_API_KEY"):
            return {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-sonnet-20240229",
                "source": "environment",
            }

        return None

    def _load_gemini_config(self) -> Optional[Dict[str, Any]]:
        """Load Gemini CLI configuration."""
        possible_paths = [
            self.home / ".config" / "gemini" / "config.json",
            self.home / ".config" / "google" / "application_default_credentials.json",
            self.home / ".gemini",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        if path.suffix == ".json":
                            config = json.load(f)
                            api_key = config.get("api_key") or config.get("key")
                        else:
                            api_key = f.read().strip()

                        return {
                            "api_key": api_key
                            or os.getenv("GEMINI_API_KEY")
                            or os.getenv("GOOGLE_API_KEY"),
                            "model": "gemini-1.5-pro",
                            "source": str(path),
                        }
                except Exception:
                    continue

        return None

    def _load_openrouter_config(self) -> Optional[Dict[str, Any]]:
        """Load OpenRouter configuration."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            return {
                "api_key": api_key,
                "model": os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo"),
                "source": "environment",
            }

        # Check common paths
        possible_paths = [
            self.home / ".openrouter_api_key",
            self.home / ".config" / "openrouter" / "key",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        return {
                            "api_key": f.read().strip(),
                            "model": "openai/gpt-3.5-turbo",
                            "source": str(path),
                        }
                except Exception:
                    continue

        return None

    def _load_openai_config(self) -> Optional[Dict[str, Any]]:
        """Load OpenAI configuration."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return {
                "api_key": api_key,
                "model": "gpt-3.5-turbo",
                "source": "environment",
            }

        # Check common paths
        possible_paths = [
            self.home / ".openai_api_key",
            self.home / ".config" / "openai" / "key",
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        return {
                            "api_key": f.read().strip(),
                            "model": "gpt-3.5-turbo",
                            "source": str(path),
                        }
                except Exception:
                    continue

        return None


class ProviderRouter:
    """Smart routing engine for AI providers."""

    def __init__(self):
        self.config_manager = ConfigInheritanceManager()
        self.providers = self._initialize_providers()
        self.cost_cache = {}

    def _initialize_providers(self) -> Dict[ProviderType, ProviderConfig]:
        """Initialize provider configurations."""
        discovered = self.config_manager.discover_existing_configs()

        providers = {}

        # OpenRouter (primary router)
        # Always initialize OpenRouter with a placeholder, even if no API key
        if ProviderType.OPENROUTER in discovered:
            providers[ProviderType.OPENROUTER] = ProviderConfig(
                provider_type=ProviderType.OPENROUTER,
                api_key=discovered[ProviderType.OPENROUTER]["api_key"],
                base_url="https://openrouter.ai/api/v1",
                models=[
                    "agentica-org/deepcoder-14b-preview:free",
                    "meta-llama/llama-3.1-8b-instruct:free",
                    "microsoft/wizardlm-2-8x22b:free",
                    "openai/gpt-3.5-turbo",
                    "anthropic/claude-3-sonnet-20240229",
                ],
                cost_data=ProviderCost(
                    input_cost_per_1k=0.0,  # Free models cost $0
                    output_cost_per_1k=0.0,  # Free models cost $0
                    speed_score=9.0,  # Free models are fast
                    capability_score={
                        TaskType.CODING: 8.5,  # Good for coding with deepcoder
                        TaskType.WRITING: 8.0,
                        TaskType.ANALYSIS: 8.0,
                        TaskType.CREATIVE: 7.5,
                        TaskType.REASONING: 8.0,
                    },
                ),
            )
        else:
            # Initialize with placeholder config for demo purposes
            providers[ProviderType.OPENROUTER] = ProviderConfig(
                provider_type=ProviderType.OPENROUTER,
                api_key=None,  # No API key
                base_url="https://openrouter.ai/api/v1",
                models=[
                    "agentica-org/deepcoder-14b-preview:free",
                    "meta-llama/llama-3.1-8b-instruct:free",
                    "microsoft/wizardlm-2-8x22b:free",
                    "openai/gpt-3.5-turbo",
                    "anthropic/claude-3-sonnet-20240229",
                ],
                cost_data=ProviderCost(
                    input_cost_per_1k=0.0,  # Free models cost $0
                    output_cost_per_1k=0.0,  # Free models cost $0
                    speed_score=9.0,  # Free models are fast
                    capability_score={
                        TaskType.CODING: 8.5,  # Good for coding with deepcoder
                        TaskType.WRITING: 8.0,
                        TaskType.ANALYSIS: 8.0,
                        TaskType.CREATIVE: 7.5,
                        TaskType.REASONING: 8.0,
                    },
                ),
                enabled=False,  # Mark as disabled since no API key
            )

        # Anthropic (direct)
        if ProviderType.ANTHROPIC in discovered:
            providers[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                api_key=discovered[ProviderType.ANTHROPIC]["api_key"],
                base_url="https://api.anthropic.com",
                models=["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                cost_data=ProviderCost(
                    input_cost_per_1k=0.003,
                    output_cost_per_1k=0.015,
                    speed_score=7.0,
                    capability_score={
                        TaskType.CODING: 9.5,
                        TaskType.WRITING: 9.5,
                        TaskType.ANALYSIS: 9.0,
                        TaskType.CREATIVE: 9.0,
                        TaskType.REASONING: 9.5,
                    },
                ),
            )

        # OpenAI (direct)
        if ProviderType.OPENAI in discovered:
            providers[ProviderType.OPENAI] = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                api_key=discovered[ProviderType.OPENAI]["api_key"],
                base_url="https://api.openai.com/v1",
                models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                cost_data=ProviderCost(
                    input_cost_per_1k=0.001,
                    output_cost_per_1k=0.002,
                    speed_score=9.0,
                    capability_score={
                        TaskType.CODING: 8.5,
                        TaskType.WRITING: 8.0,
                        TaskType.ANALYSIS: 8.5,
                        TaskType.CREATIVE: 8.0,
                        TaskType.REASONING: 8.5,
                    },
                ),
            )

        # Gemini (direct)
        if ProviderType.GEMINI in discovered:
            providers[ProviderType.GEMINI] = ProviderConfig(
                provider_type=ProviderType.GEMINI,
                api_key=discovered[ProviderType.GEMINI]["api_key"],
                base_url="https://generativelanguage.googleapis.com/v1beta",
                models=["gemini-1.5-pro", "gemini-1.5-flash"],
                cost_data=ProviderCost(
                    input_cost_per_1k=0.00025,
                    output_cost_per_1k=0.00075,
                    speed_score=9.5,
                    capability_score={
                        TaskType.CODING: 8.0,
                        TaskType.WRITING: 8.5,
                        TaskType.ANALYSIS: 9.0,
                        TaskType.CREATIVE: 8.5,
                        TaskType.REASONING: 8.5,
                    },
                ),
            )

        return providers

    def get_optimal_provider(
        self,
        task_type: TaskType,
        estimated_tokens: int = 1000,
        max_cost: Optional[float] = None,
        require_speed: bool = False,
    ) -> Tuple[ProviderType, str, float]:
        """
        Get the optimal provider for a task.

        Returns (provider_type, model_name, estimated_cost)
        """
        if not self.providers:
            raise RuntimeError("No providers configured. Run: doorman config doctor")

        doorman_config = get_config()
        user_max_cost = max_cost or doorman_config.max_cost_per_plan

        candidates = []

        for provider_type, config in self.providers.items():
            if not config.enabled or not config.api_key:
                continue

            # Calculate cost
            cost_data = config.cost_data
            estimated_cost = (estimated_tokens / 1000) * (
                cost_data.input_cost_per_1k + cost_data.output_cost_per_1k
            )

            if estimated_cost > user_max_cost:
                continue

            # Calculate capability score
            capability_score = cost_data.capability_score.get(task_type, 5.0)
            speed_score = cost_data.speed_score if require_speed else 5.0

            # Combined score (lower cost = better, higher capability/speed = better)
            # Normalize cost to 0-10 scale (inverse)
            cost_score = max(0, 10 - (estimated_cost * 1000))  # Adjust scaling
            combined_score = (
                (capability_score * 0.5) + (cost_score * 0.3) + (speed_score * 0.2)
            )

            candidates.append(
                (
                    provider_type,
                    config.models[0],  # Use primary model
                    estimated_cost,
                    combined_score,
                )
            )

        if not candidates:
            # If no candidates with API keys, return a fallback for demo purposes
            for provider_type, config in self.providers.items():
                if config.models:
                    return provider_type, config.models[0], 0.0

        if not candidates:
            raise RuntimeError(
                f"No suitable providers for task type {task_type.value} within budget ${user_max_cost}"
            )

        # Sort by combined score (highest first)
        candidates.sort(key=lambda x: x[3], reverse=True)

        best = candidates[0]
        return best[0], best[1], best[2]

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all configured providers."""
        discovered = self.config_manager.discover_existing_configs()

        status = {
            "total_providers": len(self.providers),
            "active_providers": len(
                [p for p in self.providers.values() if p.enabled and p.api_key]
            ),
            "discovered_configs": list(discovered.keys()),
            "providers": {},
        }

        for provider_type, config in self.providers.items():
            status["providers"][provider_type.value] = {
                "enabled": config.enabled,
                "has_api_key": bool(config.api_key),
                "models_available": len(config.models),
                "speed_score": config.cost_data.speed_score,
                "source": discovered.get(provider_type, {}).get(
                    "source", "not_configured"
                ),
            }

        return status

    def estimate_task_cost(
        self,
        task_type: TaskType,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
    ) -> Dict[ProviderType, float]:
        """Estimate cost across all providers for comparison."""
        costs = {}

        for provider_type, config in self.providers.items():
            if not config.enabled or not config.api_key:
                continue

            cost_data = config.cost_data
            total_cost = (
                estimated_input_tokens / 1000
            ) * cost_data.input_cost_per_1k + (
                estimated_output_tokens / 1000
            ) * cost_data.output_cost_per_1k
            costs[provider_type] = total_cost

        return costs


# Global router instance
_router: Optional[ProviderRouter] = None


def get_provider_router() -> ProviderRouter:
    """Get the global provider router."""
    global _router
    if _router is None:
        _router = ProviderRouter()
    return _router
