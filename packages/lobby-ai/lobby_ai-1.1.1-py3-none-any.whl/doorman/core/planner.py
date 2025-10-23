"""Core planning engine with intelligent provider routing and billing integration."""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from rich.console import Console
from rich.progress import Progress

from ..billing.clerk_integration import (
    check_quota_limit,
    get_clerk_client,
    get_user_billing_info,
)
from ..config.manager import get_config
from ..providers.router import TaskType, get_provider_router

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class PlanNode:
    """Node in a plan execution graph."""

    id: str
    task: str
    depends_on: List[str]
    estimated_tokens: int
    estimated_cost: float
    provider: str
    model: str
    task_type: str


@dataclass
class ExecutionPlan:
    """Complete execution plan for a user intent."""

    plan_id: str
    user_id: str
    intent: str
    category: str
    confidence: float
    nodes: List[PlanNode]
    total_tokens: int
    total_cost: float
    estimated_time: int  # seconds
    created_at: datetime
    provider_used: str
    routing_optimized: bool


class Planner:
    """Core planner engine with intelligent routing."""

    def __init__(self, user_id: Optional[str] = None):
        self.router = get_provider_router()
        self.clerk_client = get_clerk_client()
        self.config = get_config()

        # Use provided user_id or default from config
        self.user_id = user_id or self.config.user_id or "default_user"

        # Get user billing
        self.billing = get_user_billing_info(self.user_id)
        self.max_cost_per_plan = self.billing.usage_limits.get("cost_per_plan", 0.05)

    def create_plan(
        self,
        intent: str,
        require_speed: bool = False,
        override_task_type: Optional[str] = None,
        max_cost: Optional[float] = None,
    ) -> ExecutionPlan:
        """
        Create an execution plan for a user intent with intelligent routing.

        Args:
            intent: User intent to plan for
            require_speed: Prioritize speed over cost
            override_task_type: Override automatic task type classification
            max_cost: Override max cost per plan

        Returns:
            ExecutionPlan: Complete execution plan
        """
        # First check quota
        allowed, quota_info = check_quota_limit(self.user_id)
        if not allowed:
            # Fail gracefully with informative message
            daily_limit = quota_info["daily_usage"]["limit"]
            monthly_limit = quota_info["monthly_usage"]["limit"]

            console.print(
                "\n⚠️  [bold red]Usage quota exceeded![/] Unable to create plan."
            )

            if quota_info["daily_usage"]["percentage"] >= 100:
                console.print(
                    f"Daily limit reached: {quota_info['daily_usage']['used']}/{daily_limit}"
                )

            if quota_info["monthly_usage"]["percentage"] >= 100:
                console.print(
                    f"Monthly limit reached: {quota_info['monthly_usage']['used']}/{monthly_limit}"
                )

            console.print("\n💳 Consider upgrading to Premium for higher limits:")
            console.print("   doorman providers plans")
            console.print("📊 Check your current status: doorman providers billing")

            raise RuntimeError(f"Usage quota exceeded. Tier: {quota_info['tier']}")

        # Classify the task type
        task_type = self._classify_task_type(intent, override_task_type)

        # Get optimal provider for this task
        # Default token estimate - will be refined
        estimated_tokens = 1500

        # Use override cost if provided, otherwise use from billing
        cost_limit = max_cost or self.max_cost_per_plan

        # Route to optimal provider
        provider_type, model, estimated_cost = self.router.get_optimal_provider(
            task_type=task_type,
            estimated_tokens=estimated_tokens,
            max_cost=cost_limit,
            require_speed=require_speed,
        )

        # Create execution plan
        with Progress() as progress:
            # Show progress bar for plan generation
            task = progress.add_task("[cyan]Generating plan...", total=100)

            # First phase: Generate plan structure (30%)
            progress.update(task, advance=10)
            time.sleep(0.5)  # Simulate work
            progress.update(task, advance=20)

            # Set up plan ID and tracking
            plan_id = str(uuid.uuid4())
            created_at = datetime.now()

            # Generate plan nodes (this would call the actual LLM provider)
            nodes = self._generate_plan_nodes(
                intent=intent,
                task_type=task_type,
                provider_type=provider_type,
                model=model,
            )

            # Update progress
            progress.update(task, advance=40)
            time.sleep(0.3)  # Simulate work

            # Calculate totals
            total_tokens = sum(node.estimated_tokens for node in nodes)
            total_cost = sum(node.estimated_cost for node in nodes)
            estimated_time = self._estimate_execution_time(nodes, task_type)

            # Final progress update
            progress.update(task, advance=30)

        # Create full execution plan
        plan = ExecutionPlan(
            plan_id=plan_id,
            user_id=self.user_id,
            intent=intent,
            category=task_type.value,
            confidence=0.9,  # Could be calculated from model's confidence
            nodes=nodes,
            total_tokens=total_tokens,
            total_cost=total_cost,
            estimated_time=estimated_time,
            created_at=created_at,
            provider_used=provider_type.value,
            routing_optimized=True,
        )

        # Record usage for billing/analytics (would normally persist to database)
        self._record_usage(plan)

        return plan

    def _classify_task_type(
        self, intent: str, override: Optional[str] = None
    ) -> TaskType:
        """Classify intent into task type for routing."""
        if override:
            try:
                return TaskType(override.lower())
            except ValueError:
                # Invalid override, fall back to auto-classification
                pass

        # Simple heuristic classification
        intent_lower = intent.lower()

        if any(
            word in intent_lower
            for word in ["code", "program", "script", "debug", "api", "function"]
        ):
            return TaskType.CODING
        elif any(
            word in intent_lower
            for word in ["write", "blog", "article", "content", "copy"]
        ):
            return TaskType.WRITING
        elif any(
            word in intent_lower
            for word in ["analyze", "research", "study", "compare", "evaluate"]
        ):
            return TaskType.ANALYSIS
        elif any(
            word in intent_lower
            for word in ["create", "design", "brainstorm", "imagine", "story"]
        ):
            return TaskType.CREATIVE
        else:
            return TaskType.REASONING

    def _generate_plan_nodes(
        self, intent: str, task_type: TaskType, provider_type, model: str
    ) -> List[PlanNode]:
        """
        Generate plan nodes (steps) for execution.

        This would normally call the provider's API to decompose the task.
        For now, this is a simplified simulation.
        """
        # Simulate plan generation with a few steps
        # In a real implementation, this would call the provider's API

        # Basic task decomposition patterns based on task type
        if task_type == TaskType.CODING:
            steps = [
                ("Analyze requirements", [], 200),
                ("Research API documentation", [], 300),
                ("Write code structure", ["0"], 400),
                ("Implement core functionality", ["1", "2"], 600),
                ("Add error handling", ["3"], 300),
                ("Write tests", ["3"], 400),
            ]
        elif task_type == TaskType.WRITING:
            steps = [
                ("Research topic", [], 300),
                ("Create outline", ["0"], 200),
                ("Write first draft", ["1"], 800),
                ("Edit and refine", ["2"], 400),
                ("Add citations and references", ["2"], 300),
            ]
        elif task_type == TaskType.ANALYSIS:
            steps = [
                ("Gather data", [], 300),
                ("Clean and prepare data", ["0"], 400),
                ("Perform analysis", ["1"], 600),
                ("Generate visualizations", ["2"], 400),
                ("Write conclusions", ["2", "3"], 500),
            ]
        elif task_type == TaskType.CREATIVE:
            steps = [
                ("Brainstorm ideas", [], 400),
                ("Create initial draft", ["0"], 600),
                ("Refine concept", ["1"], 400),
                ("Add details and polish", ["2"], 500),
            ]
        else:  # REASONING
            steps = [
                ("Define problem scope", [], 300),
                ("Research background information", ["0"], 400),
                ("Analyze alternatives", ["1"], 500),
                ("Formulate recommendations", ["2"], 600),
                ("Create action plan", ["3"], 400),
            ]

        # Use provider's cost data to estimate costs
        provider_config = self.router.providers.get(provider_type)
        cost_data = provider_config.cost_data

        # Create nodes
        nodes = []
        for i, (task, depends_on, tokens) in enumerate(steps):
            # Calculate cost based on provider's rates
            cost = (tokens / 1000) * (
                cost_data.input_cost_per_1k + cost_data.output_cost_per_1k
            )

            # Create node
            node = PlanNode(
                id=str(i),
                task=f"{task}: {intent}" if i == len(steps) - 1 else task,
                depends_on=depends_on,
                estimated_tokens=tokens,
                estimated_cost=cost,
                provider=provider_type.value,
                model=model,
                task_type=task_type.value,
            )
            nodes.append(node)

        return nodes

    def _estimate_execution_time(
        self, nodes: List[PlanNode], task_type: TaskType
    ) -> int:
        """Estimate execution time in seconds based on plan nodes."""
        # Simple estimation based on token count and task type
        token_time_ratio = {
            TaskType.CODING: 0.05,  # Seconds per token for coding tasks
            TaskType.WRITING: 0.03,  # Writing tasks
            TaskType.ANALYSIS: 0.04,  # Analysis tasks
            TaskType.CREATIVE: 0.035,  # Creative tasks
            TaskType.REASONING: 0.045,  # Reasoning tasks
        }

        total_tokens = sum(node.estimated_tokens for node in nodes)
        base_time = total_tokens * token_time_ratio.get(task_type, 0.04)

        # Add overhead for complex dependency graphs
        dependency_complexity = len([n for n in nodes if n.depends_on])
        overhead = dependency_complexity * 10  # 10 seconds per dependency

        return int(base_time + overhead)

    def _record_usage(self, plan: ExecutionPlan) -> None:
        """Record usage for billing and analytics purposes."""
        # In a real implementation, this would update a database
        # For now, just log the usage
        logger.info(
            f"Plan created: {plan.plan_id} | "
            f"User: {plan.user_id} | "
            f"Tokens: {plan.total_tokens} | "
            f"Cost: ${plan.total_cost:.4f} | "
            f"Provider: {plan.provider_used}"
        )


def create_plan(
    intent: str,
    user_id: Optional[str] = None,
    require_speed: bool = False,
    override_task_type: Optional[str] = None,
    max_cost: Optional[float] = None,
) -> ExecutionPlan:
    """
    Create an execution plan for a user intent.

    This is the main entry point for the planning engine.
    """
    planner = Planner(user_id)
    return planner.create_plan(
        intent=intent,
        require_speed=require_speed,
        override_task_type=override_task_type,
        max_cost=max_cost,
    )


def display_plan(plan: ExecutionPlan) -> None:
    """Display an execution plan in the terminal."""
    console.print("\n")
    console.print("╔══════════════════════════════════════╗", style="bright_cyan")
    console.print("║ DOORMAN.EXE ▮▮▮ EXECUTION PLAN ▮▮▮  ║", style="bright_cyan")
    console.print("╚══════════════════════════════════════╝", style="bright_cyan")

    # Plan header
    console.print("\n▮▮▮ PROCESSING INTENT ▮▮▮")
    console.print(f"Input: {plan.intent}")
    console.print(f"Category: {plan.category}")
    console.print(f"Confidence: {plan.confidence * 100:.1f}%")

    # Provider info
    console.print("\n▮▮▮ PROVIDER INFO ▮▮▮")
    console.print(f"Provider: {plan.provider_used.upper()}")
    console.print(f"Routing: {'Optimized ✅' if plan.routing_optimized else 'Default'}")

    # Plan details
    console.print("\n▮▮▮ EXECUTION PLAN ▮▮▮")
    console.print(f"📋 Plan ID: {plan.plan_id}")
    console.print(f"⏱️  Estimated time: {plan.estimated_time // 60} minutes")
    console.print(f"💰 Estimated cost: ${plan.total_cost:.4f}")
    console.print(f"🔤 Estimated tokens: {plan.total_tokens}")

    # Plan steps
    console.print("\n🔧 Steps to Execute:")
    for i, node in enumerate(plan.nodes):
        depends = (
            f" (depends on steps {', '.join(node.depends_on)})"
            if node.depends_on
            else ""
        )
        console.print(f"  {i + 1}. {node.task}{depends}")
