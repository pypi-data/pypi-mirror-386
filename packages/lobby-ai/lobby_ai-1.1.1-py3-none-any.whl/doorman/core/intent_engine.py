"""Token-optimized intent classification and taxonomy generation."""

from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from doorman.core.taxonomy import (
    Assumption,
    ClarificationQuestion,
    Component,
    ComponentType,
    ConfidenceLevel,
    IntentTaxonomy,
)


class IntentClassifier:
    """Lightweight intent classification using embeddings and templates."""

    def __init__(self):
        self.templates = self._load_cached_templates()
        self.embedding_cache = {}

    def classify_intent(self, user_input: str) -> Tuple[str, float, str]:
        """
        Classify intent using minimal tokens.

        Returns:
            (intent, confidence, category)
        """
        # Quick keyword matching first (0 tokens)
        category = self._quick_category_match(user_input)

        # For specific patterns, don't use template matching to avoid overrides
        # Just use the original intent
        return user_input.strip(), 0.8, category

    def _quick_category_match(self, text: str) -> str:
        """Zero-token category classification using keywords."""
        text_lower = text.lower()

        category_keywords = {
            "coding": [
                "code",
                "program",
                "debug",
                "api",
                "function",
                "script",
                "app",
                "create",
                "build",
                "develop",
                "react",
                "node",
                "python",
                "install",
                "setup",
                "deploy",
                "git",
                "npm",
                "yarn",
                "docker",
                "kubernetes",
                "database",
            ],
            "food": [
                "eat",
                "cook",
                "recipe",
                "food",
                "meal",
                "sandwich",
                "dinner",
                "lunch",
                "breakfast",
            ],
            "business": [
                "meeting",
                "project",
                "task",
                "email",
                "report",
                "client",
                "presentation",
                "proposal",
                "budget",
            ],
            "creative": [
                "write",
                "design",
                "art",
                "blog",
                "content",
                "story",
                "video",
                "music",
                "photo",
            ],
            "research": [
                "find",
                "search",
                "analyze",
                "research",
                "investigate",
                "study",
                "learn",
                "explore",
            ],
            "personal": [
                "buy",
                "schedule",
                "book",
                "plan",
                "organize",
                "remind",
                "calendar",
                "appointment",
            ],
            "devops": [
                "deploy",
                "server",
                "nginx",
                "apache",
                "aws",
                "cloud",
                "infrastructure",
                "monitoring",
                "backup",
            ],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return "general"

    def _find_template_match(self, text: str, category: str) -> Optional[Dict]:
        """Find matching cached template (0 tokens)."""
        # Simple similarity matching - in production, use embeddings
        for template in self.templates.get(category, []):
            if any(keyword in text.lower() for keyword in template["keywords"]):
                return {
                    "intent": template["pattern"],
                    "confidence": template["success_rate"],
                    "template_id": template["id"],
                }
        return None

    def _llm_classify(self, text: str, category: str) -> Tuple[str, float, str]:
        """Minimal token LLM classification."""
        # This would use OpenRouter with a very focused prompt
        # For now, return heuristic
        confidence = 0.7 if len(text.split()) > 3 else 0.5
        return text.strip(), confidence, category

    def _load_cached_templates(self) -> Dict[str, List[Dict]]:
        """Load pre-computed templates to avoid LLM calls."""
        return {
            "food": [
                {
                    "id": str(uuid4()),
                    "pattern": "make food item",
                    "keywords": ["make", "cook", "prepare"],
                    "success_rate": 0.85,
                }
            ],
            "coding": [
                {
                    "id": str(uuid4()),
                    "pattern": "create software",
                    "keywords": ["create", "build", "code"],
                    "success_rate": 0.90,
                }
            ],
        }


class TaxonomyGenerator:
    """Generate task taxonomy with minimal token usage."""

    def __init__(self):
        self.component_templates = self._load_component_templates()
        self.structured_prompt_cache = {}

    async def generate_taxonomy(
        self, intent: str, category: str, confidence: float
    ) -> IntentTaxonomy:
        """
        Generate taxonomy using structured generation and caching.
        """
        # Try template-based generation first (0 tokens)
        if confidence > 0.8:
            template_taxonomy = self._generate_from_template(intent, category)
            if template_taxonomy:
                return template_taxonomy

        # Use structured LLM generation (optimized tokens)
        return await self._structured_llm_generation(intent, category, confidence)

    def _generate_from_template(
        self, intent: str, category: str
    ) -> Optional[IntentTaxonomy]:
        """Generate taxonomy from cached templates (0 tokens)."""
        templates = self.component_templates.get(category, {})

        if category == "food" and "make" in intent.lower():
            return IntentTaxonomy(
                intent=intent,
                intent_category=category,
                context_confidence=0.85,
                confidence_level=ConfidenceLevel.HIGH,
                components=[
                    Component(
                        type=ComponentType.INGREDIENT,
                        name="main_ingredient",
                        description=f"Primary ingredient for {intent}",
                        required=True,
                    ),
                    Component(
                        type=ComponentType.TOOL,
                        name="preparation_tools",
                        description="Tools needed for preparation",
                        required=True,
                    ),
                    Component(
                        type=ComponentType.RECIPE,
                        name="instructions",
                        description="Step-by-step preparation guide",
                        required=True,
                    ),
                ],
                assumptions=[
                    Assumption(
                        description="User has access to kitchen", confidence=0.8
                    ),
                    Assumption(
                        description="No dietary restrictions",
                        confidence=0.6,
                        fallback_strategy="Ask about allergies and preferences",
                    ),
                ],
                clarification_questions=[
                    ClarificationQuestion(
                        question="Do you have any dietary restrictions?",
                        question_type="multiple_choice",
                        options=["None", "Vegetarian", "Vegan", "Gluten-free", "Other"],
                    )
                ],
                estimated_total_time_minutes=30,
                complexity_score=3,
            )

        return None

    async def _structured_llm_generation(
        self, intent: str, category: str, confidence: float
    ) -> IntentTaxonomy:
        """Use structured generation with JSON schema and real OpenRouter API calls."""
        from ..core.models import get_user_id
        from ..providers.openrouter import (
            get_structured_generator,
        )

        # JSON schema for structured output
        schema = {
            "type": "object",
            "properties": {
                "components": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {
                                "enum": [
                                    "tool",
                                    "ingredient",
                                    "recipe",
                                    "environment",
                                    "skill",
                                    "validation",
                                ]
                            },
                            "description": {"type": "string"},
                            "required": {"type": "boolean"},
                            "alternatives": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["name", "type", "description", "required"],
                    },
                },
                "assumptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": ["description", "confidence"],
                    },
                },
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "options": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["question"],
                    },
                },
                "estimated_time_minutes": {"type": "integer", "minimum": 1},
                "complexity_score": {"type": "number", "minimum": 1, "maximum": 10},
            },
            "required": [
                "components",
                "assumptions",
                "estimated_time_minutes",
                "complexity_score",
            ],
        }

        # Optimized prompt for token efficiency
        prompt = f"""Break down the task: "{intent}" (category: {category})

Generate a task decomposition with:
- Components needed (tools, skills, ingredients, etc.)
- Assumptions about user's context
- Clarification questions if needed
- Time estimate and complexity (1-10)

Be specific and actionable. Focus on executable steps."""

        try:
            # Get user ID for usage tracking
            user_id = get_user_id()

            # Use structured generator with OpenRouter
            generator = await get_structured_generator()
            json_response = await generator.generate_json(
                prompt=prompt,
                schema=schema,
                model="openai/gpt-3.5-turbo",  # Fast and cost-effective
                user_id=user_id,
                max_retries=2,
            )

            # Convert JSON response to IntentTaxonomy
            components = []
            for comp in json_response.get("components", []):
                components.append(
                    Component(
                        type=ComponentType(comp["type"]),
                        name=comp["name"],
                        description=comp["description"],
                        required=comp["required"],
                        alternatives=comp.get("alternatives", []),
                    )
                )

            assumptions = []
            for assump in json_response.get("assumptions", []):
                assumptions.append(
                    Assumption(
                        description=assump["description"],
                        confidence=assump["confidence"],
                    )
                )

            questions = []
            for q in json_response.get("questions", []):
                questions.append(
                    ClarificationQuestion(
                        question=q["question"], options=q.get("options", [])
                    )
                )

            return IntentTaxonomy(
                intent=intent,
                intent_category=category,
                context_confidence=confidence,
                confidence_level=ConfidenceLevel.MEDIUM
                if confidence < 0.8
                else ConfidenceLevel.HIGH,
                components=components,
                assumptions=assumptions,
                clarification_questions=questions,
                estimated_total_time_minutes=json_response.get(
                    "estimated_time_minutes", 15
                ),
                complexity_score=json_response.get("complexity_score", 4),
            )

        except Exception as e:
            # Fallback to simple taxonomy if OpenRouter fails
            print(f"OpenRouter API call failed: {e}")
            return IntentTaxonomy(
                intent=intent,
                intent_category=category,
                context_confidence=confidence,
                confidence_level=ConfidenceLevel.LOW,
                components=[
                    Component(
                        type=ComponentType.TOOL,
                        name="primary_tool",
                        description="Main tool/resource required",
                        required=True,
                    )
                ],
                assumptions=[
                    Assumption(
                        description="User has basic setup and permissions",
                        confidence=0.7,
                    )
                ],
                estimated_total_time_minutes=15,
                complexity_score=4,
            )

    def _load_component_templates(self) -> Dict[str, Dict]:
        """Load component templates for each category."""
        return {
            "food": {
                "common_tools": ["knife", "cutting_board", "pan", "plate"],
                "common_ingredients": ["salt", "pepper", "oil"],
                "environments": ["kitchen", "dining_area"],
            },
            "coding": {
                "common_tools": ["editor", "terminal", "browser", "debugger"],
                "environments": ["development_machine", "repository"],
                "skills": ["programming", "debugging", "testing"],
            },
        }


class ConfidenceEngine:
    """Manage confidence scoring and validation."""

    def __init__(self):
        self.confidence_thresholds = {
            "auto_execute": 0.9,
            "ask_clarification": 0.6,
            "require_validation": 0.4,
        }

    def should_ask_clarification(self, taxonomy: IntentTaxonomy) -> bool:
        """Determine if clarification questions should be shown."""
        return (
            taxonomy.context_confidence
            < self.confidence_thresholds["ask_clarification"]
            or len(taxonomy.clarification_questions) > 0
        )

    def validate_taxonomy(self, taxonomy: IntentTaxonomy) -> List[str]:
        """Validate taxonomy completeness and consistency."""
        issues = []

        if not taxonomy.components:
            issues.append("No components identified")

        if taxonomy.context_confidence < 0.5:
            issues.append("Low confidence in intent classification")

        required_components = [c for c in taxonomy.components if c.required]
        if not required_components:
            issues.append("No required components identified")

        return issues

    def suggest_improvements(self, taxonomy: IntentTaxonomy) -> List[str]:
        """Suggest ways to improve the taxonomy."""
        suggestions = []

        if taxonomy.context_confidence < 0.8:
            suggestions.append("Consider asking clarification questions")

        if not taxonomy.assumptions:
            suggestions.append("Add explicit assumptions")

        if taxonomy.complexity_score < 3:
            suggestions.append("Consider breaking into more detailed steps")

        return suggestions
