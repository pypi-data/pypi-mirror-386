"""Universal taxonomy schema for intent decomposition."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence levels for intent classification."""

    LOW = "low"  # < 0.6
    MEDIUM = "medium"  # 0.6 - 0.8
    HIGH = "high"  # > 0.8


class DependencyType(str, Enum):
    """Types of dependencies between components."""

    SEQUENTIAL = "sequential"  # A must complete before B
    PARALLEL = "parallel"  # A and B can run simultaneously
    CONDITIONAL = "conditional"  # B only runs if A meets criteria
    FEEDBACK = "feedback"  # Results of B affect parameters of A


class ComponentType(str, Enum):
    """Types of components in a taxonomy."""

    TOOL = "tool"  # Physical or digital tool
    INGREDIENT = "ingredient"  # Raw material or input
    RECIPE = "recipe"  # Step-by-step instructions
    ENVIRONMENT = "environment"  # Required context or setting
    SKILL = "skill"  # Required capability or knowledge
    VALIDATION = "validation"  # Check or verification step


class Component(BaseModel):
    """A component needed for intent execution."""

    id: UUID = Field(default_factory=uuid4)
    type: ComponentType
    name: str
    description: Optional[str] = None

    # Nested components (e.g., ingredients have sub-ingredients)
    components: List["Component"] = Field(default_factory=list)

    # MCP integration
    mcp_server: Optional[str] = None
    mcp_tool: Optional[str] = None

    # Validation
    required: bool = True
    alternatives: List[str] = Field(default_factory=list)

    # Metadata
    cost_estimate: Optional[float] = None
    time_estimate_minutes: Optional[int] = None


class Assumption(BaseModel):
    """An assumption made during intent decomposition."""

    id: UUID = Field(default_factory=uuid4)
    description: str
    confidence: float = Field(ge=0.0, le=1.0)

    # If assumption is false, what happens?
    fallback_strategy: Optional[str] = None
    validation_method: Optional[str] = None


class ClarificationQuestion(BaseModel):
    """A question to ask the user for clarification."""

    id: UUID = Field(default_factory=uuid4)
    question: str
    question_type: str = "multiple_choice"  # open_ended, yes_no, multiple_choice
    options: List[str] = Field(default_factory=list)

    # Impact of answer on taxonomy
    affects_components: List[UUID] = Field(default_factory=list)
    affects_assumptions: List[UUID] = Field(default_factory=list)


class Dependency(BaseModel):
    """A dependency relationship between components."""

    id: UUID = Field(default_factory=uuid4)
    from_component: UUID
    to_component: UUID
    dependency_type: DependencyType

    # Conditional logic
    condition: Optional[str] = None  # "if from_component.status == 'success'"
    weight: float = 1.0  # Importance of this dependency


class IntentTaxonomy(BaseModel):
    """Complete decomposition of a user intent."""

    id: UUID = Field(default_factory=uuid4)

    # Core intent
    intent: str
    intent_category: Optional[str] = None  # "food", "coding", "business", etc.

    # Classification confidence
    context_confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel

    # Decomposition
    components: List[Component] = Field(default_factory=list)
    dependencies: List[Dependency] = Field(default_factory=list)
    assumptions: List[Assumption] = Field(default_factory=list)

    # User interaction
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)

    # Execution metadata
    estimated_total_time_minutes: Optional[int] = None
    estimated_total_cost: Optional[float] = None
    complexity_score: int = Field(ge=1, le=10, default=5)

    # Tracking
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    execution_status: str = "pending"  # pending, running, completed, failed

    # Token optimization
    embedding: Optional[List[float]] = None  # For similarity matching
    template_id: Optional[UUID] = None  # If based on cached template


class TaxonomyTemplate(BaseModel):
    """Cached template for common intent patterns."""

    id: UUID = Field(default_factory=uuid4)

    # Template matching
    pattern: str  # Regex or embedding-based pattern
    category: str
    keywords: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None

    # Template structure
    component_templates: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    common_assumptions: List[Dict[str, Any]] = Field(default_factory=list)

    # Usage tracking
    usage_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None


# Enable forward references
Component.model_rebuild()
