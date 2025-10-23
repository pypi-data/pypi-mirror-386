"""Pattern library for reusable workflow templates and task decomposition."""

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from pydantic import BaseModel

from doorman.core.models import IntentCategory


@dataclass
class Pattern:
    """A reusable workflow pattern."""

    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    components: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    estimated_time_minutes: int
    complexity_score: float
    success_rate: float
    usage_count: int
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None
    template_variables: Optional[Dict[str, str]] = None


class PatternSearchRequest(BaseModel):
    """Request for pattern search."""

    query: str
    category: Optional[str] = None
    max_results: int = 10
    min_similarity: float = 0.3
    include_embeddings: bool = False


class PatternSearchResult(BaseModel):
    """Result from pattern search."""

    pattern_id: str
    similarity_score: float
    pattern: Dict[str, Any]


class PatternLibrary:
    """Manages workflow patterns with embedding-based search."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".doorman" / "patterns"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.patterns_file = self.data_dir / "patterns.json"
        self.embeddings_file = self.data_dir / "embeddings.json"
        self._patterns: Dict[str, Pattern] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from disk."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file) as f:
                    data = json.load(f)
                    patterns = {}
                    for pid, pattern_data in data.items():
                        # Convert ISO strings back to datetime objects
                        if "created_at" in pattern_data:
                            pattern_data["created_at"] = datetime.fromisoformat(
                                pattern_data["created_at"]
                            )
                        if "updated_at" in pattern_data:
                            pattern_data["updated_at"] = datetime.fromisoformat(
                                pattern_data["updated_at"]
                            )
                        patterns[pid] = Pattern(**pattern_data)
                    self._patterns = patterns
            except Exception as e:
                print(f"Warning: Failed to load patterns: {e}")
                self._patterns = {}

        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file) as f:
                    self._embeddings = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load embeddings: {e}")
                self._embeddings = {}

        # Initialize with seed patterns if empty
        if not self._patterns:
            self._initialize_seed_patterns()

    def _save_patterns(self) -> None:
        """Save patterns to disk."""
        try:
            # Convert patterns to serializable format
            data = {}
            for pid, pattern in self._patterns.items():
                pattern_dict = asdict(pattern)
                # Convert datetime objects to ISO strings
                pattern_dict["created_at"] = pattern.created_at.isoformat()
                pattern_dict["updated_at"] = pattern.updated_at.isoformat()
                data[pid] = pattern_dict

            with open(self.patterns_file, "w") as f:
                json.dump(data, f, indent=2)

            with open(self.embeddings_file, "w") as f:
                json.dump(self._embeddings, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save patterns: {e}")

    def _initialize_seed_patterns(self) -> None:
        """Initialize with seed patterns for common workflows."""
        seed_patterns = [
            {
                "name": "Blog Post Creation",
                "description": "Complete workflow for creating high-quality blog posts from research to publication",
                "category": "writing",
                "tags": ["blog", "content", "writing", "research", "seo"],
                "components": [
                    {
                        "name": "topic_research",
                        "type": "research",
                        "description": "Research topic and keywords",
                    },
                    {
                        "name": "outline_creation",
                        "type": "planning",
                        "description": "Create detailed outline",
                    },
                    {
                        "name": "draft_writing",
                        "type": "writing",
                        "description": "Write first draft",
                    },
                    {
                        "name": "editing_revision",
                        "type": "editing",
                        "description": "Edit and revise content",
                    },
                    {
                        "name": "seo_optimization",
                        "type": "optimization",
                        "description": "Optimize for SEO",
                    },
                    {
                        "name": "publication",
                        "type": "publishing",
                        "description": "Publish and promote",
                    },
                ],
                "dependencies": [
                    {
                        "from": "topic_research",
                        "to": "outline_creation",
                        "type": "sequential",
                    },
                    {
                        "from": "outline_creation",
                        "to": "draft_writing",
                        "type": "sequential",
                    },
                    {
                        "from": "draft_writing",
                        "to": "editing_revision",
                        "type": "sequential",
                    },
                    {
                        "from": "editing_revision",
                        "to": "seo_optimization",
                        "type": "sequential",
                    },
                    {
                        "from": "seo_optimization",
                        "to": "publication",
                        "type": "sequential",
                    },
                ],
                "estimated_time_minutes": 180,
                "complexity_score": 0.6,
                "template_variables": {
                    "topic": "Main topic or keyword",
                    "target_audience": "Primary audience",
                    "word_count": "Target word count",
                },
            },
            {
                "name": "REST API Development",
                "description": "Complete REST API development workflow from design to deployment",
                "category": "coding",
                "tags": ["api", "development", "backend", "rest", "documentation"],
                "components": [
                    {
                        "name": "api_design",
                        "type": "design",
                        "description": "Design API endpoints and schemas",
                    },
                    {
                        "name": "database_setup",
                        "type": "infrastructure",
                        "description": "Set up database schema",
                    },
                    {
                        "name": "authentication",
                        "type": "security",
                        "description": "Implement authentication",
                    },
                    {
                        "name": "endpoint_implementation",
                        "type": "coding",
                        "description": "Implement API endpoints",
                    },
                    {
                        "name": "testing",
                        "type": "testing",
                        "description": "Write and run tests",
                    },
                    {
                        "name": "documentation",
                        "type": "documentation",
                        "description": "Create API documentation",
                    },
                    {
                        "name": "deployment",
                        "type": "deployment",
                        "description": "Deploy to production",
                    },
                ],
                "dependencies": [
                    {
                        "from": "api_design",
                        "to": "database_setup",
                        "type": "sequential",
                    },
                    {
                        "from": "database_setup",
                        "to": "authentication",
                        "type": "sequential",
                    },
                    {
                        "from": "authentication",
                        "to": "endpoint_implementation",
                        "type": "sequential",
                    },
                    {
                        "from": "endpoint_implementation",
                        "to": "testing",
                        "type": "sequential",
                    },
                    {"from": "testing", "to": "documentation", "type": "parallel"},
                    {"from": "documentation", "to": "deployment", "type": "sequential"},
                ],
                "estimated_time_minutes": 480,
                "complexity_score": 0.8,
                "template_variables": {
                    "framework": "Backend framework (FastAPI, Express, etc.)",
                    "database": "Database type",
                    "auth_method": "Authentication method",
                },
            },
            {
                "name": "Data Analysis Project",
                "description": "End-to-end data analysis workflow from data collection to insights",
                "category": "analysis",
                "tags": ["data", "analysis", "visualization", "insights", "reporting"],
                "components": [
                    {
                        "name": "data_collection",
                        "type": "collection",
                        "description": "Gather and import data",
                    },
                    {
                        "name": "data_cleaning",
                        "type": "preprocessing",
                        "description": "Clean and validate data",
                    },
                    {
                        "name": "exploratory_analysis",
                        "type": "analysis",
                        "description": "Explore data patterns",
                    },
                    {
                        "name": "statistical_analysis",
                        "type": "analysis",
                        "description": "Perform statistical tests",
                    },
                    {
                        "name": "visualization",
                        "type": "visualization",
                        "description": "Create charts and graphs",
                    },
                    {
                        "name": "insights_report",
                        "type": "reporting",
                        "description": "Compile insights and recommendations",
                    },
                ],
                "dependencies": [
                    {
                        "from": "data_collection",
                        "to": "data_cleaning",
                        "type": "sequential",
                    },
                    {
                        "from": "data_cleaning",
                        "to": "exploratory_analysis",
                        "type": "sequential",
                    },
                    {
                        "from": "exploratory_analysis",
                        "to": "statistical_analysis",
                        "type": "parallel",
                    },
                    {
                        "from": "exploratory_analysis",
                        "to": "visualization",
                        "type": "parallel",
                    },
                    {
                        "from": "statistical_analysis",
                        "to": "insights_report",
                        "type": "sequential",
                    },
                    {
                        "from": "visualization",
                        "to": "insights_report",
                        "type": "sequential",
                    },
                ],
                "estimated_time_minutes": 240,
                "complexity_score": 0.7,
                "template_variables": {
                    "data_source": "Primary data source",
                    "analysis_type": "Type of analysis needed",
                    "tools": "Preferred analysis tools",
                },
            },
            {
                "name": "Research Project",
                "description": "Academic or professional research workflow from literature review to publication",
                "category": "research",
                "tags": [
                    "research",
                    "literature",
                    "methodology",
                    "analysis",
                    "publication",
                ],
                "components": [
                    {
                        "name": "literature_review",
                        "type": "research",
                        "description": "Review existing literature",
                    },
                    {
                        "name": "methodology_design",
                        "type": "planning",
                        "description": "Design research methodology",
                    },
                    {
                        "name": "data_collection",
                        "type": "collection",
                        "description": "Collect research data",
                    },
                    {
                        "name": "analysis",
                        "type": "analysis",
                        "description": "Analyze findings",
                    },
                    {
                        "name": "writing",
                        "type": "writing",
                        "description": "Write research paper",
                    },
                    {
                        "name": "peer_review",
                        "type": "review",
                        "description": "Submit for peer review",
                    },
                ],
                "dependencies": [
                    {
                        "from": "literature_review",
                        "to": "methodology_design",
                        "type": "sequential",
                    },
                    {
                        "from": "methodology_design",
                        "to": "data_collection",
                        "type": "sequential",
                    },
                    {"from": "data_collection", "to": "analysis", "type": "sequential"},
                    {"from": "analysis", "to": "writing", "type": "sequential"},
                    {"from": "writing", "to": "peer_review", "type": "sequential"},
                ],
                "estimated_time_minutes": 720,
                "complexity_score": 0.9,
                "template_variables": {
                    "research_topic": "Main research question",
                    "methodology": "Research methodology",
                    "target_journal": "Target publication venue",
                },
            },
            {
                "name": "Product Launch",
                "description": "Complete product launch workflow from planning to post-launch analysis",
                "category": "project_management",
                "tags": ["product", "launch", "marketing", "coordination", "analysis"],
                "components": [
                    {
                        "name": "launch_planning",
                        "type": "planning",
                        "description": "Plan launch strategy",
                    },
                    {
                        "name": "marketing_materials",
                        "type": "marketing",
                        "description": "Create marketing content",
                    },
                    {
                        "name": "team_coordination",
                        "type": "coordination",
                        "description": "Coordinate teams",
                    },
                    {
                        "name": "pre_launch_testing",
                        "type": "testing",
                        "description": "Final testing and QA",
                    },
                    {
                        "name": "launch_execution",
                        "type": "execution",
                        "description": "Execute launch",
                    },
                    {
                        "name": "post_launch_analysis",
                        "type": "analysis",
                        "description": "Analyze launch metrics",
                    },
                ],
                "dependencies": [
                    {
                        "from": "launch_planning",
                        "to": "marketing_materials",
                        "type": "parallel",
                    },
                    {
                        "from": "launch_planning",
                        "to": "team_coordination",
                        "type": "parallel",
                    },
                    {
                        "from": "marketing_materials",
                        "to": "pre_launch_testing",
                        "type": "sequential",
                    },
                    {
                        "from": "team_coordination",
                        "to": "pre_launch_testing",
                        "type": "sequential",
                    },
                    {
                        "from": "pre_launch_testing",
                        "to": "launch_execution",
                        "type": "sequential",
                    },
                    {
                        "from": "launch_execution",
                        "to": "post_launch_analysis",
                        "type": "sequential",
                    },
                ],
                "estimated_time_minutes": 960,
                "complexity_score": 0.85,
                "template_variables": {
                    "product_name": "Product being launched",
                    "launch_date": "Target launch date",
                    "team_size": "Team size and roles",
                },
            },
            {
                "name": "CRM Workflow Automation",
                "description": "Automate customer relationship management processes and workflows",
                "category": "automation",
                "tags": ["crm", "automation", "workflows", "customer", "sales"],
                "components": [
                    {
                        "name": "process_mapping",
                        "type": "analysis",
                        "description": "Map existing CRM processes",
                    },
                    {
                        "name": "automation_design",
                        "type": "design",
                        "description": "Design automation workflows",
                    },
                    {
                        "name": "integration_setup",
                        "type": "integration",
                        "description": "Set up system integrations",
                    },
                    {
                        "name": "workflow_implementation",
                        "type": "implementation",
                        "description": "Implement automated workflows",
                    },
                    {
                        "name": "testing_validation",
                        "type": "testing",
                        "description": "Test automation workflows",
                    },
                    {
                        "name": "team_training",
                        "type": "training",
                        "description": "Train team on new processes",
                    },
                ],
                "dependencies": [
                    {
                        "from": "process_mapping",
                        "to": "automation_design",
                        "type": "sequential",
                    },
                    {
                        "from": "automation_design",
                        "to": "integration_setup",
                        "type": "sequential",
                    },
                    {
                        "from": "integration_setup",
                        "to": "workflow_implementation",
                        "type": "sequential",
                    },
                    {
                        "from": "workflow_implementation",
                        "to": "testing_validation",
                        "type": "sequential",
                    },
                    {
                        "from": "testing_validation",
                        "to": "team_training",
                        "type": "sequential",
                    },
                ],
                "estimated_time_minutes": 300,
                "complexity_score": 0.7,
                "template_variables": {
                    "crm_system": "CRM platform being used",
                    "processes": "Specific processes to automate",
                    "integrations": "Required integrations",
                },
            },
        ]

        now = datetime.now()
        for i, pattern_data in enumerate(seed_patterns):
            pattern_id = str(uuid4())
            pattern = Pattern(
                id=pattern_id,
                name=pattern_data["name"],
                description=pattern_data["description"],
                category=pattern_data["category"],
                tags=pattern_data["tags"],
                components=pattern_data["components"],
                dependencies=pattern_data["dependencies"],
                estimated_time_minutes=pattern_data["estimated_time_minutes"],
                complexity_score=pattern_data["complexity_score"],
                success_rate=0.85 + (i * 0.02),  # Vary success rates
                usage_count=0,
                created_at=now,
                updated_at=now,
                template_variables=pattern_data.get("template_variables", {}),
            )
            self._patterns[pattern_id] = pattern

        self._save_patterns()

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using OpenRouter or fallback to keyword extraction."""
        import os

        # Try OpenRouter first if API key available
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/embeddings",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "HTTP-Referer": "https://doorman.dev",
                            "X-Title": "Doorman Pattern Library",
                        },
                        json={"model": "text-embedding-ada-002", "input": text},
                        timeout=10.0,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data["data"][0]["embedding"]
            except Exception as e:
                print(f"Warning: Failed to get OpenRouter embedding: {e}")

        # Fallback to simple keyword-based "embedding" (TF-IDF style)
        return self._simple_text_embedding(text)

    def _simple_text_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Create simple text embedding based on word frequencies."""
        import hashlib
        import math

        words = text.lower().split()
        word_counts = {}
        for word in words:
            # Remove punctuation and count
            clean_word = "".join(c for c in word if c.isalnum())
            if clean_word:
                word_counts[clean_word] = word_counts.get(clean_word, 0) + 1

        # Create embedding vector using hash-based positioning
        embedding = [0.0] * dim
        total_words = len(words)

        for word, count in word_counts.items():
            # Hash word to get consistent position
            hash_val = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            positions = [
                hash_val % dim,
                (hash_val // dim) % dim,
                (hash_val // (dim * 2)) % dim,
            ]

            # TF-IDF style score (simplified)
            tf = count / total_words
            weight = tf * math.log(1 + total_words)  # Simplified IDF

            for pos in positions:
                embedding[pos] += weight

        # Normalize vector
        magnitude = math.sqrt(sum(x**2 for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x**2 for x in a))
        magnitude_b = math.sqrt(sum(x**2 for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    async def search_patterns(
        self, request: PatternSearchRequest
    ) -> List[PatternSearchResult]:
        """Search patterns using embedding similarity and keyword matching."""
        query_embedding = await self.get_embedding(request.query)
        results = []

        for pattern_id, pattern in self._patterns.items():
            # Calculate similarity score
            similarity_score = 0.0

            if query_embedding:
                # Get pattern embedding (generate if not exists)
                pattern_text = (
                    f"{pattern.name} {pattern.description} {' '.join(pattern.tags)}"
                )
                pattern_embedding = self._embeddings.get(pattern_id)

                if not pattern_embedding:
                    pattern_embedding = await self.get_embedding(pattern_text)
                    if pattern_embedding:
                        self._embeddings[pattern_id] = pattern_embedding
                        self._save_patterns()

                if pattern_embedding:
                    similarity_score = self._cosine_similarity(
                        query_embedding, pattern_embedding
                    )

            # Keyword matching fallback/boost
            query_lower = request.query.lower()
            keyword_score = 0.0

            if query_lower in pattern.name.lower():
                keyword_score += 0.5
            if query_lower in pattern.description.lower():
                keyword_score += 0.3
            if any(query_lower in tag.lower() for tag in pattern.tags):
                keyword_score += 0.2

            # Combined score
            combined_score = max(similarity_score, keyword_score)

            # Category filter
            if request.category and pattern.category != request.category:
                combined_score *= 0.1  # Heavily penalize wrong category

            # Minimum similarity threshold
            if combined_score >= request.min_similarity:
                pattern_dict = asdict(pattern)
                pattern_dict["created_at"] = pattern.created_at.isoformat()
                pattern_dict["updated_at"] = pattern.updated_at.isoformat()

                # Remove embedding from response unless requested
                if not request.include_embeddings:
                    pattern_dict["embedding"] = None

                results.append(
                    PatternSearchResult(
                        pattern_id=pattern_id,
                        similarity_score=combined_score,
                        pattern=pattern_dict,
                    )
                )

        # Sort by similarity score and limit results
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[: request.max_results]

    async def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)

    async def add_pattern(self, pattern: Pattern) -> str:
        """Add a new pattern to the library."""
        pattern_id = pattern.id or str(uuid4())
        pattern.id = pattern_id
        pattern.created_at = datetime.now()
        pattern.updated_at = datetime.now()

        self._patterns[pattern_id] = pattern

        # Generate embedding for new pattern
        pattern_text = f"{pattern.name} {pattern.description} {' '.join(pattern.tags)}"
        embedding = await self.get_embedding(pattern_text)
        if embedding:
            self._embeddings[pattern_id] = embedding

        self._save_patterns()
        return pattern_id

    async def update_pattern_usage(self, pattern_id: str) -> None:
        """Increment usage count for a pattern."""
        if pattern_id in self._patterns:
            self._patterns[pattern_id].usage_count += 1
            self._patterns[pattern_id].updated_at = datetime.now()
            self._save_patterns()

    def get_popular_patterns(self, limit: int = 10) -> List[Tuple[str, Pattern]]:
        """Get most popular patterns by usage count."""
        sorted_patterns = sorted(
            self._patterns.items(), key=lambda x: x[1].usage_count, reverse=True
        )
        return sorted_patterns[:limit]

    def get_patterns_by_category(self, category: str) -> List[Tuple[str, Pattern]]:
        """Get all patterns in a specific category."""
        return [
            (pid, pattern)
            for pid, pattern in self._patterns.items()
            if pattern.category == category
        ]

    async def suggest_patterns_for_intent(
        self, intent: str, category: IntentCategory
    ) -> List[PatternSearchResult]:
        """Suggest patterns based on classified intent and category."""
        # Map intent categories to search queries
        category_queries = {
            IntentCategory.CODING: "development programming code software",
            IntentCategory.WRITING: "writing content blog article documentation",
            IntentCategory.ANALYSIS: "data analysis research insights statistics",
            IntentCategory.RESEARCH: "research study investigation literature",
            IntentCategory.PROJECT_MANAGEMENT: "project management coordination planning",
            IntentCategory.DESIGN: "design create visual interface",
            IntentCategory.AUTOMATION: "automation workflow process integration",
            IntentCategory.LEARNING: "learning education training tutorial",
        }

        # Combine intent with category-specific keywords
        search_query = f"{intent} {category_queries.get(category, '')}"

        request = PatternSearchRequest(
            query=search_query,
            category=category.value if category != IntentCategory.OTHER else None,
            max_results=5,
            min_similarity=0.2,
        )

        return await self.search_patterns(request)


# Global pattern library instance
_pattern_library: Optional[PatternLibrary] = None


def get_pattern_library() -> PatternLibrary:
    """Get global pattern library instance."""
    global _pattern_library
    if _pattern_library is None:
        _pattern_library = PatternLibrary()
    return _pattern_library
