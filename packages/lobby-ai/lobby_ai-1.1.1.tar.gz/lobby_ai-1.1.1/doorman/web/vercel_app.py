"""Vercel-compatible FastAPI app wrapper."""

import os

from .app import create_app

# Set production environment variables
os.environ.setdefault("BASE_URL", "https://api.doorman.dev")
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///tmp/doorman.db"
)  # Use PlanetScale or Supabase in prod

# Create FastAPI app
app = create_app()

# Vercel expects this variable name
handler = app
