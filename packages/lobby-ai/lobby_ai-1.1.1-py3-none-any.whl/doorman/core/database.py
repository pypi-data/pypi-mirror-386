"""SurrealDB database configuration and schema management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from surrealdb import Surreal

from doorman.core.models import User, UserTier
from doorman.core.taxonomy import IntentTaxonomy


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = "memory"  # For development
    namespace: str = "doorman"
    database: str = "main"
    username: Optional[str] = None
    password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        data_dir = Path.home() / ".doorman"
        data_dir.mkdir(exist_ok=True)

        # Default to file-based SurrealDB for local development
        default_url = f"file://{data_dir}/doorman.db"

        return cls(
            url=os.getenv("DOORMAN_DATABASE_URL", default_url),
            namespace=os.getenv("DOORMAN_DB_NAMESPACE", "doorman"),
            database=os.getenv("DOORMAN_DB_NAME", "main"),
            username=os.getenv("DOORMAN_DB_USERNAME"),
            password=os.getenv("DOORMAN_DB_PASSWORD"),
        )


class SurrealDBManager:
    """Manages SurrealDB connections and operations."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db: Optional[Surreal] = None

    async def connect(self) -> None:
        """Connect to SurrealDB."""
        if self.db is not None:
            # Already connected
            return

        self.db = Surreal()
        await self.db.connect(self.config.url)

        if self.config.username and self.config.password:
            await self.db.signin(
                {"user": self.config.username, "pass": self.config.password}
            )

        await self.db.use(self.config.namespace, self.config.database)

    async def disconnect(self) -> None:
        """Disconnect from SurrealDB."""
        if self.db:
            await self.db.close()
            self.db = None

    async def initialize_schema(self) -> None:
        """Initialize database schema and tables."""
        if not self.db:
            await self.connect()

        # Define table schemas using SurrealQL
        schemas = [
            # Users table
            """
            DEFINE TABLE users SCHEMAFULL;
            DEFINE FIELD id ON users TYPE record<users>;
            DEFINE FIELD email ON users TYPE option<string>;
            DEFINE FIELD handle ON users TYPE option<string>;
            DEFINE FIELD created_at ON users TYPE datetime DEFAULT time::now();
            DEFINE FIELD tier ON users TYPE string DEFAULT "free";
            DEFINE FIELD license_key_hash ON users TYPE option<string>;
            DEFINE FIELD feature_flags ON users TYPE object DEFAULT {};
            DEFINE FIELD plans_used_today ON users TYPE int DEFAULT 0;
            DEFINE FIELD plans_used_this_month ON users TYPE int DEFAULT 0;
            DEFINE FIELD quota_reset_date ON users TYPE option<datetime>;
            DEFINE INDEX idx_users_email ON users COLUMNS email;
            """,
            # API Keys table
            """
            DEFINE TABLE api_keys SCHEMAFULL;
            DEFINE FIELD id ON api_keys TYPE record<api_keys>;
            DEFINE FIELD user_id ON api_keys TYPE record<users>;
            DEFINE FIELD provider ON api_keys TYPE string;
            DEFINE FIELD label ON api_keys TYPE string;
            DEFINE FIELD encrypted_value ON api_keys TYPE string;
            DEFINE FIELD created_at ON api_keys TYPE datetime DEFAULT time::now();
            DEFINE INDEX idx_api_keys_user ON api_keys COLUMNS user_id;
            DEFINE INDEX idx_api_keys_provider ON api_keys COLUMNS provider;
            """,
            # Intent Taxonomies table
            """
            DEFINE TABLE taxonomies SCHEMAFULL;
            DEFINE FIELD id ON taxonomies TYPE record<taxonomies>;
            DEFINE FIELD user_id ON taxonomies TYPE record<users>;
            DEFINE FIELD intent ON taxonomies TYPE string;
            DEFINE FIELD intent_category ON taxonomies TYPE option<string>;
            DEFINE FIELD context_confidence ON taxonomies TYPE float;
            DEFINE FIELD confidence_level ON taxonomies TYPE string;
            DEFINE FIELD components ON taxonomies TYPE array<object>;
            DEFINE FIELD dependencies ON taxonomies TYPE array<object>;
            DEFINE FIELD assumptions ON taxonomies TYPE array<object>;
            DEFINE FIELD clarification_questions ON taxonomies TYPE array<object>;
            DEFINE FIELD estimated_total_time_minutes ON taxonomies TYPE option<int>;
            DEFINE FIELD complexity_score ON taxonomies TYPE int DEFAULT 5;
            DEFINE FIELD created_at ON taxonomies TYPE datetime DEFAULT time::now();
            DEFINE FIELD execution_status ON taxonomies TYPE string DEFAULT "pending";
            DEFINE FIELD embedding ON taxonomies TYPE option<array<float>>;
            DEFINE INDEX idx_taxonomies_user ON taxonomies COLUMNS user_id;
            DEFINE INDEX idx_taxonomies_category ON taxonomies COLUMNS intent_category;
            """,
            # Usage Ledger table
            """
            DEFINE TABLE usage_ledger SCHEMAFULL;
            DEFINE FIELD id ON usage_ledger TYPE record<usage_ledger>;
            DEFINE FIELD user_id ON usage_ledger TYPE record<users>;
            DEFINE FIELD taxonomy_id ON usage_ledger TYPE option<record<taxonomies>>;
            DEFINE FIELD provider ON usage_ledger TYPE string;
            DEFINE FIELD model ON usage_ledger TYPE string;
            DEFINE FIELD input_tokens ON usage_ledger TYPE int;
            DEFINE FIELD output_tokens ON usage_ledger TYPE int;
            DEFINE FIELD cost_usd_estimated ON usage_ledger TYPE option<float>;
            DEFINE FIELD source ON usage_ledger TYPE string;
            DEFINE FIELD created_at ON usage_ledger TYPE datetime DEFAULT time::now();
            DEFINE INDEX idx_usage_user ON usage_ledger COLUMNS user_id;
            DEFINE INDEX idx_usage_provider ON usage_ledger COLUMNS provider;
            """,
            # Taxonomy Templates table
            """
            DEFINE TABLE taxonomy_templates SCHEMAFULL;
            DEFINE FIELD id ON taxonomy_templates TYPE record<taxonomy_templates>;
            DEFINE FIELD pattern ON taxonomy_templates TYPE string;
            DEFINE FIELD category ON taxonomy_templates TYPE string;
            DEFINE FIELD keywords ON taxonomy_templates TYPE array<string>;
            DEFINE FIELD embedding ON taxonomy_templates TYPE option<array<float>>;
            DEFINE FIELD component_templates ON taxonomy_templates TYPE array<object>;
            DEFINE FIELD dependency_patterns ON taxonomy_templates TYPE array<object>;
            DEFINE FIELD common_assumptions ON taxonomy_templates TYPE array<object>;
            DEFINE FIELD usage_count ON taxonomy_templates TYPE int DEFAULT 0;
            DEFINE FIELD success_rate ON taxonomy_templates TYPE float DEFAULT 0.0;
            DEFINE FIELD last_used ON taxonomy_templates TYPE option<datetime>;
            DEFINE INDEX idx_templates_category ON taxonomy_templates COLUMNS category;
            """,
            # Billing Subscriptions table
            """
            DEFINE TABLE billing_subscriptions SCHEMAFULL;
            DEFINE FIELD id ON billing_subscriptions TYPE record<billing_subscriptions>;
            DEFINE FIELD user_id ON billing_subscriptions TYPE record<users>;
            DEFINE FIELD provider ON billing_subscriptions TYPE string DEFAULT "stripe";
            DEFINE FIELD status ON billing_subscriptions TYPE string;
            DEFINE FIELD product ON billing_subscriptions TYPE string;
            DEFINE FIELD seats ON billing_subscriptions TYPE int DEFAULT 1;
            DEFINE FIELD renews_at ON billing_subscriptions TYPE option<datetime>;
            DEFINE FIELD customer_ref ON billing_subscriptions TYPE option<string>;
            DEFINE INDEX idx_billing_user ON billing_subscriptions COLUMNS user_id;
            """,
        ]

        # Execute schema definitions
        for schema in schemas:
            await self.db.query(schema)

    # Simple CRUD interface for billing system
    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a record in the specified table."""
        if not self.db:
            await self.connect()

        result = await self.db.create(table, data)
        return result[0] if result else {}

    async def select(self, table: str, condition: str = None) -> List[Dict[str, Any]]:
        """Select records from the specified table."""
        if not self.db:
            await self.connect()

        if condition:
            query = f"SELECT * FROM {table} WHERE {condition}"
        else:
            query = f"SELECT * FROM {table}"

        result = await self.db.query(query)
        return result[0]["result"] if result and result[0]["result"] else []

    async def update(
        self, table: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a record in the specified table."""
        if not self.db:
            await self.connect()

        result = await self.db.update(f"{table}:{record_id}", data)
        return result[0] if result else {}

    async def delete(self, table: str, record_id: str) -> bool:
        """Delete a record from the specified table."""
        if not self.db:
            await self.connect()

        result = await self.db.delete(f"{table}:{record_id}")
        return bool(result)

    async def query(
        self, sql: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a custom SQL query."""
        if not self.db:
            await self.connect()

        result = await self.db.query(sql, params or {})
        return result[0]["result"] if result and result[0]["result"] else []

    async def get_or_create_user(
        self, email: Optional[str] = None, handle: Optional[str] = None
    ) -> User:
        """Get or create a user."""
        if not self.db:
            await self.connect()

        # For single-user mode, create default user
        result = await self.db.query("SELECT * FROM users LIMIT 1")

        if result and result[0]["result"]:
            user_data = result[0]["result"][0]
            return User(
                id=UUID(user_data["id"].split(":")[1]),
                email=user_data.get("email"),
                handle=user_data.get("handle"),
                created_at=datetime.fromisoformat(
                    user_data["created_at"].replace("Z", "+00:00")
                ),
                tier=UserTier(user_data.get("tier", "free")),
                feature_flags=user_data.get("feature_flags", {}),
                plans_used_today=user_data.get("plans_used_today", 0),
                plans_used_this_month=user_data.get("plans_used_this_month", 0),
            )

        # Create new user
        user = User(email=email, handle=handle)
        user_data = {
            "id": f"users:{user.id}",
            "email": user.email,
            "handle": user.handle,
            "created_at": user.created_at.isoformat(),
            "tier": user.tier.value,
            "feature_flags": user.feature_flags,
            "plans_used_today": user.plans_used_today,
            "plans_used_this_month": user.plans_used_this_month,
        }

        await self.db.create("users", user_data)
        return user

    async def save_taxonomy(self, taxonomy: IntentTaxonomy, user_id: UUID) -> str:
        """Save a taxonomy to the database."""
        if not self.db:
            await self.connect()

        taxonomy_data = {
            "id": f"taxonomies:{taxonomy.id}",
            "user_id": f"users:{user_id}",
            "intent": taxonomy.intent,
            "intent_category": taxonomy.intent_category,
            "context_confidence": taxonomy.context_confidence,
            "confidence_level": taxonomy.confidence_level.value,
            "components": [c.model_dump() for c in taxonomy.components],
            "dependencies": [d.model_dump() for d in taxonomy.dependencies],
            "assumptions": [a.model_dump() for a in taxonomy.assumptions],
            "clarification_questions": [
                q.model_dump() for q in taxonomy.clarification_questions
            ],
            "estimated_total_time_minutes": taxonomy.estimated_total_time_minutes,
            "complexity_score": taxonomy.complexity_score,
            "created_at": taxonomy.created_at.isoformat(),
            "execution_status": taxonomy.execution_status,
            "embedding": taxonomy.embedding,
        }

        result = await self.db.create("taxonomies", taxonomy_data)
        return result[0]["id"]

    async def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get taxonomy templates by category."""
        if not self.db:
            await self.connect()

        query = "SELECT * FROM taxonomy_templates WHERE category = $category ORDER BY success_rate DESC"
        result = await self.db.query(query, {"category": category})

        if result and result[0]["result"]:
            return result[0]["result"]
        return []

    async def record_usage(
        self,
        user_id: UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        source: str,
        taxonomy_id: Optional[UUID] = None,
        cost_usd_estimated: Optional[float] = None,
    ) -> None:
        """Record token usage."""
        if not self.db:
            await self.connect()

        usage_data = {
            "user_id": f"users:{user_id}",
            "taxonomy_id": f"taxonomies:{taxonomy_id}" if taxonomy_id else None,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd_estimated": cost_usd_estimated,
            "source": source,
            "created_at": datetime.now().isoformat(),
        }

        await self.db.create("usage_ledger", usage_data)

    async def get_user_usage_today(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's usage statistics for today."""
        if not self.db:
            await self.connect()

        query = """
        SELECT 
            count() as total_requests,
            sum(input_tokens) as total_input_tokens,
            sum(output_tokens) as total_output_tokens,
            sum(cost_usd_estimated) as total_cost_usd
        FROM usage_ledger 
        WHERE user_id = $user_id AND created_at > time::now() - 1d
        """

        result = await self.db.query(query, {"user_id": f"users:{user_id}"})

        if result and result[0]["result"]:
            return result[0]["result"][0]

        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
        }


# Global database manager instance
db_manager: Optional[SurrealDBManager] = None


async def get_db() -> SurrealDBManager:
    """Get database manager instance."""
    global db_manager
    if db_manager is None:
        try:
            config = DatabaseConfig.from_env()
            db_manager = SurrealDBManager(config)
        except Exception as e:
            # If database initialization fails, create a mock manager
            print(f"Failed to initialize database: {e}")
            return None
    return db_manager


# Global database instance
_db_instance = None


async def get_database() -> Optional[SurrealDBManager]:
    """Get global database instance."""
    global _db_instance

    if _db_instance is None:
        try:
            config = DatabaseConfig.from_env()
            _db_instance = SurrealDBManager(config)
            await _db_instance.connect()
            await _db_instance.initialize_schema()
        except Exception as e:
            # If database initialization fails, return None
            print(f"Failed to initialize database: {e}")
            return None

    return _db_instance


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[Optional[SurrealDBManager], None]:
    """Get database session context manager."""
    try:
        db = await get_database()
        if db and not db.db:
            await db.connect()
        yield db
    except Exception as e:
        print(f"Database session error: {e}")
        yield None


async def init_database() -> None:
    """Initialize database schema."""
    db = await get_db()
    await db.initialize_schema()
