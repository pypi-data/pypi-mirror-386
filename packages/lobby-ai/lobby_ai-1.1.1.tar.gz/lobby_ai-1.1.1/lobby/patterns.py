"""
Pattern and template management for LOBBY CLI.
Provides reusable task patterns with interactive management.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TaskPattern:
    """Reusable task pattern/template."""

    id: str
    name: str
    category: str
    description: str
    agent: str
    model: Optional[str]
    tools: List[str]
    template: str
    variables: Dict[str, str]  # Variable name -> description
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "agent": self.agent,
            "model": self.model,
            "tools": self.tools,
            "template": self.template,
            "variables": self.variables,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskPattern":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            category=data["category"],
            description=data["description"],
            agent=data["agent"],
            model=data.get("model"),
            tools=data.get("tools", []),
            template=data["template"],
            variables=data.get("variables", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            usage_count=data.get("usage_count", 0),
        )


class PatternManager:
    """Manage task patterns and templates."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize pattern manager."""
        if db_path is None:
            config_dir = Path.home() / ".config" / "lobby"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = config_dir / "patterns.db"

        self.db_path = str(db_path)
        self.init_db()
        self.load_default_patterns()

    def init_db(self):
        """Initialize patterns database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                agent TEXT,
                model TEXT,
                tools TEXT,  -- JSON array
                template TEXT NOT NULL,
                variables TEXT,  -- JSON object
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_category 
            ON patterns(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_name 
            ON patterns(name)
        """)

        conn.commit()
        conn.close()

    def load_default_patterns(self):
        """Load default patterns if database is empty."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM patterns")
        count = cursor.fetchone()[0]

        if count == 0:
            # Add default patterns
            default_patterns = [
                TaskPattern(
                    id=str(uuid.uuid4()),
                    name="Code Review",
                    category="development",
                    description="Comprehensive code review with best practices",
                    agent="developer",
                    model="auto",
                    tools=["code-execution", "git-operations"],
                    template="Review the code in {file_path} focusing on:\n1. Code quality and best practices\n2. Potential bugs or issues\n3. Performance optimizations\n4. Security considerations\n5. Suggestions for improvement",
                    variables={"file_path": "Path to the file to review"},
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                TaskPattern(
                    id=str(uuid.uuid4()),
                    name="Blog Post",
                    category="content",
                    description="Create a blog post on a topic",
                    agent="writer",
                    model="auto",
                    tools=["web-search"],
                    template="Write a {word_count}-word blog post about {topic}.\nTarget audience: {audience}\nTone: {tone}\nInclude relevant examples and actionable insights.",
                    variables={
                        "word_count": "Target word count (e.g., 1000)",
                        "topic": "Blog post topic",
                        "audience": "Target audience",
                        "tone": "Writing tone (professional, casual, etc.)",
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                TaskPattern(
                    id=str(uuid.uuid4()),
                    name="Data Analysis",
                    category="analysis",
                    description="Analyze data and provide insights",
                    agent="analyst",
                    model="auto",
                    tools=["file-operations", "database-query"],
                    template="Analyze the data in {data_source} to:\n1. Identify key trends and patterns\n2. Calculate {metrics}\n3. Generate visualizations for {visualizations}\n4. Provide actionable recommendations",
                    variables={
                        "data_source": "Path to data file or database",
                        "metrics": "Specific metrics to calculate",
                        "visualizations": "Types of charts/graphs needed",
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                TaskPattern(
                    id=str(uuid.uuid4()),
                    name="API Client",
                    category="development",
                    description="Generate API client code",
                    agent="developer",
                    model="auto",
                    tools=["code-execution", "api-calls"],
                    template="Create a {language} client for the {api_name} API.\nInclude:\n1. Authentication handling\n2. All major endpoints\n3. Error handling and retries\n4. Type definitions/models\n5. Usage examples\nAPI Documentation: {api_docs_url}",
                    variables={
                        "language": "Programming language",
                        "api_name": "Name of the API",
                        "api_docs_url": "URL to API documentation",
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
                TaskPattern(
                    id=str(uuid.uuid4()),
                    name="Test Suite",
                    category="development",
                    description="Generate comprehensive test suite",
                    agent="developer",
                    model="auto",
                    tools=["code-execution", "file-operations"],
                    template="Create a comprehensive test suite for {component}:\n1. Unit tests for all functions/methods\n2. Integration tests for {integration_points}\n3. Edge cases and error scenarios\n4. Performance tests if applicable\nTesting framework: {framework}",
                    variables={
                        "component": "Component/module to test",
                        "integration_points": "External dependencies to test",
                        "framework": "Testing framework to use",
                    },
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                ),
            ]

            for pattern in default_patterns:
                self.save_pattern(pattern)

        conn.close()

    def save_pattern(self, pattern: TaskPattern) -> bool:
        """Save a pattern to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO patterns 
                (id, name, category, description, agent, model, tools, 
                 template, variables, created_at, updated_at, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    pattern.id,
                    pattern.name,
                    pattern.category,
                    pattern.description,
                    pattern.agent,
                    pattern.model,
                    json.dumps(pattern.tools),
                    pattern.template,
                    json.dumps(pattern.variables),
                    pattern.created_at,
                    pattern.updated_at,
                    pattern.usage_count,
                ),
            )

            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving pattern: {e}")
            return False
        finally:
            conn.close()

    def get_pattern(self, pattern_id: str) -> Optional[TaskPattern]:
        """Get a pattern by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, category, description, agent, model, tools, 
                   template, variables, created_at, updated_at, usage_count
            FROM patterns
            WHERE id = ?
        """,
            (pattern_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return TaskPattern(
                id=row[0],
                name=row[1],
                category=row[2],
                description=row[3],
                agent=row[4],
                model=row[5],
                tools=json.loads(row[6]) if row[6] else [],
                template=row[7],
                variables=json.loads(row[8]) if row[8] else {},
                created_at=datetime.fromisoformat(row[9]),
                updated_at=datetime.fromisoformat(row[10]),
                usage_count=row[11],
            )

        return None

    def list_patterns(self, category: Optional[str] = None) -> List[TaskPattern]:
        """List all patterns, optionally filtered by category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if category:
            cursor.execute(
                """
                SELECT id, name, category, description, agent, model, tools, 
                       template, variables, created_at, updated_at, usage_count
                FROM patterns
                WHERE category = ?
                ORDER BY usage_count DESC, name
            """,
                (category,),
            )
        else:
            cursor.execute("""
                SELECT id, name, category, description, agent, model, tools, 
                       template, variables, created_at, updated_at, usage_count
                FROM patterns
                ORDER BY category, usage_count DESC, name
            """)

        patterns = []
        for row in cursor.fetchall():
            patterns.append(
                TaskPattern(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    description=row[3],
                    agent=row[4],
                    model=row[5],
                    tools=json.loads(row[6]) if row[6] else [],
                    template=row[7],
                    variables=json.loads(row[8]) if row[8] else {},
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    usage_count=row[11],
                )
            )

        conn.close()
        return patterns

    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT category 
            FROM patterns 
            ORDER BY category
        """)

        categories = [row[0] for row in cursor.fetchall()]
        conn.close()

        return categories

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting pattern: {e}")
            return False
        finally:
            conn.close()

    def increment_usage(self, pattern_id: str):
        """Increment usage count for a pattern."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE patterns 
            SET usage_count = usage_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """,
            (pattern_id,),
        )

        conn.commit()
        conn.close()

    def search_patterns(self, query: str) -> List[TaskPattern]:
        """Search patterns by name or description."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        search_term = f"%{query}%"
        cursor.execute(
            """
            SELECT id, name, category, description, agent, model, tools, 
                   template, variables, created_at, updated_at, usage_count
            FROM patterns
            WHERE name LIKE ? OR description LIKE ? OR template LIKE ?
            ORDER BY usage_count DESC, name
        """,
            (search_term, search_term, search_term),
        )

        patterns = []
        for row in cursor.fetchall():
            patterns.append(
                TaskPattern(
                    id=row[0],
                    name=row[1],
                    category=row[2],
                    description=row[3],
                    agent=row[4],
                    model=row[5],
                    tools=json.loads(row[6]) if row[6] else [],
                    template=row[7],
                    variables=json.loads(row[8]) if row[8] else {},
                    created_at=datetime.fromisoformat(row[9]),
                    updated_at=datetime.fromisoformat(row[10]),
                    usage_count=row[11],
                )
            )

        conn.close()
        return patterns
