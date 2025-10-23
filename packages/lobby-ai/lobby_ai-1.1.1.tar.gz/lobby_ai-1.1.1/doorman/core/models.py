"""Core domain models for Doorman."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of AI agents available."""

    DEVELOPER = "developer"
    WRITER = "writer"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    PM = "pm"
    DESIGNER = "designer"
    SUPPORT = "support"


class ToolType(str, Enum):
    """Types of tools/integrations."""

    CODE = "code"  # GitHub, GitLab
    COMMS = "comms"  # Slack, Discord, Email
    DOCS = "docs"  # Notion, Google Docs
    DATA = "data"  # Spreadsheets, Databases
    PROJECT = "project"  # Jira, Asana, Trello
    AUTOMATION = "automation"  # Zapier, Make
    API = "api"  # REST/GraphQL APIs
    MCP = "mcp"  # MCP servers


class UserTier(str, Enum):
    """User subscription tiers."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class IntentCategory(str, Enum):
    """Categories for user intent classification."""

    CODING = "coding"
    WRITING = "writing"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    PROJECT_MANAGEMENT = "project_management"
    DESIGN = "design"
    AUTOMATION = "automation"
    LEARNING = "learning"
    OTHER = "other"


class ConfidenceLevel(str, Enum):
    """Confidence levels for intent classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Agent(BaseModel):
    """AI Agent definition."""

    id: UUID = Field(default_factory=uuid4)
    type: AgentType
    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    sprite_name: Optional[str] = None

    # Agent configuration
    system_prompt: Optional[str] = None
    model_preference: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7


class Tool(BaseModel):
    """Tool/Integration definition."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    type: ToolType
    description: str
    required_credentials: List[str] = Field(default_factory=list)
    mcp_server_url: Optional[str] = None
    api_base_url: Optional[str] = None
    documentation_url: Optional[str] = None
    is_active: bool = True


class Step(BaseModel):
    """Individual step in a task plan."""

    id: UUID = Field(default_factory=uuid4)
    order: int
    title: str
    description: str
    estimated_duration_minutes: Optional[int] = None

    # Dependencies
    depends_on: List[UUID] = Field(default_factory=list)

    # Required resources
    required_agent: Optional[AgentType] = None
    required_tools: List[str] = Field(default_factory=list)
    required_credentials: List[str] = Field(default_factory=list)

    # Execution details
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # AI context
    prompt_template: Optional[str] = None
    expected_output: Optional[str] = None


class Plan(BaseModel):
    """Complete execution plan for a task."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)

    # Plan structure
    steps: List[Step] = Field(default_factory=list)
    estimated_total_duration_minutes: Optional[int] = None

    # Resource requirements summary
    required_agents: List[AgentType] = Field(default_factory=list)
    required_tools: List[Tool] = Field(default_factory=list)
    required_credentials: List[str] = Field(default_factory=list)

    # Cost estimation
    estimated_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None

    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    progress_percentage: float = 0.0

    # Metadata for UI
    complexity_score: int = Field(ge=1, le=10, default=5)
    sprite_layout: Optional[Dict[str, Any]] = None  # For visual DAG representation


class Task(BaseModel):
    """User task to be planned and executed."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    description: str
    raw_input: str  # Original user input
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # Planning results
    plan: Optional[Plan] = None

    # Execution state
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # User preferences/constraints
    deadline: Optional[datetime] = None
    budget_limit_usd: Optional[float] = None
    privacy_level: str = "standard"  # standard, high, enterprise

    # Pattern matching
    matched_pattern_id: Optional[UUID] = None
    pattern_confidence: Optional[float] = None


class User(BaseModel):
    """User account information."""

    id: UUID = Field(default_factory=uuid4)
    email: Optional[str] = None
    handle: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    # Subscription info
    tier: UserTier = UserTier.FREE
    license_key_hash: Optional[str] = None

    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict)

    # Usage tracking
    plans_used_today: int = 0
    plans_used_this_month: int = 0
    quota_reset_date: Optional[datetime] = None


class UsageRecord(BaseModel):
    """Token usage tracking for billing."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    task_id: Optional[UUID] = None

    # Provider details
    provider: str  # "openrouter", "doorman_proxy"
    model: str

    # Usage metrics
    input_tokens: int
    output_tokens: int
    cost_usd_estimated: Optional[float] = None

    # Context
    source: str  # "cli", "mcp_client", "mcp_server"
    created_at: datetime = Field(default_factory=datetime.now)


class Pattern(BaseModel):
    """Reusable task pattern/template."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)

    # Pattern structure
    plan_template: Dict[str, Any] = Field(default_factory=dict)

    # Matching
    embedding: Optional[List[float]] = None
    example_queries: List[str] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 0
    success_rate: Optional[float] = None


def get_user_id() -> str:
    """Get current user ID (simplified for single-user mode)."""
    import hashlib
    import platform

    # Create a consistent user ID based on system info
    system_info = f"{platform.node()}:{platform.system()}:{platform.machine()}"
    user_hash = hashlib.md5(system_info.encode()).hexdigest()[:16]
    return f"user_{user_hash}"
