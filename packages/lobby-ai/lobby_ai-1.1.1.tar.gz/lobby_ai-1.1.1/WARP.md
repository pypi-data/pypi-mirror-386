# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**LOBBY** is a production-ready AI concierge service that **multiplies existing CLI tools** with intelligent orchestration. The system works as an MCP (Model Context Protocol) server that enhances Claude CLI, Gemini CLI, Cursor, and other MCP-compatible tools.

### Core Value Proposition
*"Multiply your existing CLI tools with intelligent AI orchestration"*

1. **Intelligent Routing** - Task-specific model selection with cost optimization
2. **MCP Integration** - Native protocol support for universal CLI tool compatibility
3. **Cost Optimization** - Prefers FREE models, transparent pricing
4. **CLI Tool Multiplier** - Enhances rather than replaces existing tools
5. **Production Ready** - Complete billing, usage tracking, error handling

## Core Architecture

### Tech Stack
- **CLI Framework**: Typer + Rich (professional NYC theme)
- **Database**: SQLite (usage tracking and billing)
- **Config/Data**: Pydantic models with validation
- **MCP Integration**: Python MCP SDK (server role, client detection)
- **HTTP Client**: httpx for async OpenRouter API calls
- **Model Routing**: Intelligent provider selection with cost optimization
- **Billing**: Usage-based with free tier (10 requests/day)

### Optimized Directory Structure
```
lobby/                          # Main Python package
├── __init__.py                 # Package metadata and exports
├── cli.py                      # Main CLI interface (lobby command)
└── mcp_server.py              # MCP server (lobby-mcp command)

Supporting Infrastructure:
├── doorman/                    # Legacy orchestration engine (reused)
│   ├── core/                  # Task orchestration and routing
│   ├── providers/             # OpenRouter integration
│   └── config/                # Configuration management
├── setup.py                   # PyPI package configuration
├── README.md                  # User documentation
└── openrouter_client.py       # Simple OpenRouter API wrapper
```

## Development Commands

### Environment Setup
```bash
# Install in development mode
pip install -e .

# Install with MCP dependencies
pip install -e ".[mcp]"

# Set up API key
export OPENROUTER_API_KEY="your-key-here"

# Test installation
lobby --help
```

### Development Workflow
```bash
# Run LOBBY CLI in development mode
python -m lobby.cli --help
lobby request "Create a blog post about AI agents"

# Run setup command
lobby setup

# Start MCP server
lobby-mcp
# or
python -m lobby.mcp_server

# Run validation tests
python install_test.py
python demo_installation.py

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
```

### Quality Gates
```bash
# Format and lint
ruff format .
ruff check . --fix
mypy .

# Run full test suite
pytest --cov=doorman --cov-report=html

# Test against live APIs (requires keys)
pytest tests/integration/ -m "live_api" --api-key=$OPENROUTER_API_KEY
```

## Key Components

### Intelligent Router (`doorman/providers/router.py`)
The heart of LOBBY - analyzes user input and routes to optimal AI models:

1. **Task Classification**: Categorizes tasks (coding, writing, analysis, creative, reasoning)
2. **Model Selection**: Chooses optimal AI model based on task type and cost
3. **Provider Management**: Handles OpenRouter integration with fallback options
4. **Cost Optimization**: Prefers FREE models (agentica-org/deepcoder:free, etc.)
5. **Usage Tracking**: Records token usage and costs for billing

### Billing Strategy (BYOK + Subscriptions)
- **Model Costs**: User provides OpenRouter API key; they pay directly
- **Monetization**: Usage-based pricing for orchestration service:
  - Free: 10 orchestrations/day
  - Pay-per-use: $0.01 per orchestration after free tier
  - Professional: $29/month (2,500 orchestrations)
  - Enterprise: $99/month (unlimited orchestrations)

### MCP Integration
- **Server Mode**: Exposes `orchestrate_task`, `analyze_routing`, `check_usage` tools
- **Client Detection**: Auto-discovers Claude CLI, Gemini CLI, Cursor configurations
- **Protocol Compliance**: Full MCP specification implementation with proper error handling

### Visual Theme (NYC Professional)
- **UI Design**: Professional box-drawing borders, elegant terminal layout
- **Color Scheme**: Bright cyan headers, professional table formatting
- **Branding**: NYC concierge service language and hospitality themes
- **Typography**: Rich library formatting, clean CLI interface

## Configuration

### Environment Variables
```bash
OPENROUTER_API_KEY=     # User's model provider key
DOORMAN_LICENSE_KEY=    # Premium subscription validation
DOORMAN_BACKEND_URL=    # Phase 2 billing server (optional)
DOORMAN_DATA_DIR=       # SQLite database location
```

### Key Storage
- **macOS**: Keychain Services for API keys
- **Fallback**: Encrypted local file with user password
- **License**: Cached in SQLite with online validation

## Database Schema

### Core Tables
- `users`: Single-user accounts with tier and feature flags
- `api_keys`: Encrypted provider credentials  
- `tasks`: User task history with plan JSON
- `usage_ledger`: Token consumption tracking for quotas
- `patterns`: Reusable task templates with embeddings
- `billing_subscriptions`: Stripe subscription status

### Quotas and Limits
- Daily/monthly plan count limits by tier
- Token bucket implementation in SQLite
- Feature gates checked before expensive operations

## Plugin System

### Plugin Types
1. **Agent Definitions**: Capabilities, prompts, specializations
2. **Tool Integrations**: MCP servers, REST API wrappers
3. **Billing Providers**: Future payment method extensions

### Bundled Plugins
- **Agents**: developer, writer, analyst, researcher, PM
- **Tools**: GitHub, Jira, Slack, Notion, Google Drive, Zapier
- **Integration**: MCP-first when available, REST APIs as fallback

## Testing Strategy

### Test Categories
- **Unit Tests**: Core planner logic, billing, quota enforcement
- **Integration Tests**: OpenRouter API, MCP server/client flows
- **UI Tests**: Textual TUI snapshots and interactions
- **Golden Tests**: Plan generation with fixed inputs

### Mock Strategy
- OpenRouter API responses for consistent testing
- MCP server/client mocks for integration tests  
- Stripe webhook payloads for billing tests

## Deployment and Distribution

### Packaging
- **PyPI**: Primary distribution channel
- **Homebrew**: Tap for macOS users via `pipx`/`uvx`
- **Binary**: Optional PyInstaller builds with embedded assets

### CI/CD Pipeline
```bash
# GitHub Actions workflow
- Lint and type check (ruff, mypy)
- Test matrix (Python 3.9-3.12, macOS/Linux)  
- Build and publish to PyPI on tags
- Optional: Deploy doorman-web service
```

## Security Considerations

### API Key Handling
- Never log or expose secrets in plain text
- Structured logging with automatic redaction
- Sandboxed plugin execution with timeouts

### Rate Limiting
- Per-user quotas enforced in both CLI and MCP server
- Graceful degradation when limits exceeded
- Clear upgrade prompts for premium features

## Monetization Implementation

### Feature Gating
All premium features show clear upgrade CTAs:
- Custom agent creation locked behind Premium
- Advanced routing depth requires subscription
- Team spaces and priority queue for Premium+
- Enterprise gets SSO, on-prem deployment options

### Billing UX
- Simple device-code flow for CLI authentication
- Stripe Customer Portal integration for self-service
- Clear cost breakdown: "Models billed via your OpenRouter key, features via Doorman Premium"

## Future Phases

### Phase 2: Credits System
- Optional Doorman Credits for users without OpenRouter keys
- Proxy model calls through our account with margin
- Stripe top-ups and automatic failover logic

### Phase 3: Enterprise
- White-label deployment with custom branding
- SSO integration via OIDC
- Advanced analytics and audit logging
- Custom SLA and support tiers

## Production Readiness Status

### ✅ Completed Features
- **Complete Package Structure**: PyPI-ready with proper entry points
- **MCP Server Implementation**: Full protocol compliance with 3 core tools
- **Intelligent Routing**: Task-specific model selection with FREE model priority
- **Billing System**: Usage tracking with free tier and pay-per-use pricing
- **CLI Interface**: Professional NYC-themed interface with Rich formatting
- **Installation**: Single command (`pip install lobby-ai`) with 30-second setup

### 🚀 Key Optimizations Needed

1. **Eliminate Code Duplication**
   - Multiple MCP server implementations exist
   - Consolidate into single `lobby/mcp_server.py`
   - Remove legacy doorman CLI components

2. **Fix Dependency Issues**
   - Make Stripe optional (currently breaks installation)
   - Move to `extras_require` for billing features
   - Clean up sys.path manipulation

3. **MCP Spec Compliance**
   - Ensure full MCP protocol implementation
   - Add proper error handling and validation
   - Test with Claude CLI, Cursor, Gemini CLI

4. **Package Structure**
   - Move from `setup.py` to modern `pyproject.toml`
   - Clean separation between core and optional features
   - Proper Python packaging without path hacks

## Development Tips

- **Start Simple**: MVP focuses on OpenRouter BYOK + basic orchestration
- **Test Early**: Validate MCP compliance with real CLI tools  
- **Zero Duplication**: Single source of truth for all components
- **MCP First**: Prioritize MCP integration over standalone CLI
- **Production Focus**: "Really, really easy" installation experience

### Interactive UI Development

#### Setup
```bash
# Install with interactive extras for development
pip install -e ".[interactive]"

# Test without interactive packages (fallback mode)
pip install -e .
CI=1 python -m lobby.cli --help
```

#### Key Components
- **`lobby/ui/prompts.py`**: Abstraction layer for prompts with InquirerPy/questionary/Typer fallback
- **`lobby/ui/theme.py`**: NYC Professional theme consistency between Rich and prompts
- **`lobby/patterns.py`**: Pattern management with SQLite persistence

#### Testing Interactive Features
```bash
# Run interactive tests
pytest tests/test_interactive_prompts.py -v

# Test non-interactive fallback
CI=1 pytest tests/test_interactive_prompts.py -v

# Manual testing
python test_interactive.py  # Basic functionality test
lobby --no-interactive setup  # Test non-interactive mode
```

#### Design Principles
1. **Graceful Degradation**: Always work without interactive packages
2. **MCP Non-Interactive**: MCP server must never import interactive modules
3. **Environment Detection**: Respect CI, DOORMAN_CI, TTY status
4. **Consistent Theme**: NYC Professional across all UI components
