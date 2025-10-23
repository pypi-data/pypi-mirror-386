# LOBBY CLI User Guide

## Table of Contents
1. [Installation](#installation)
2. [First Time Setup](#first-time-setup)
3. [Using LOBBY](#using-lobby)
4. [Pattern Management](#pattern-management)
5. [Advanced Features](#advanced-features)
6. [Troubleshooting](#troubleshooting)

## Installation

### Node (npx)
```bash
npx lobby-ai --help
npx lobby-ai setup
```

### Python (Minimal)
```bash
pip install lobby-ai
```
This gives you basic CLI functionality with Typer prompts.

### Interactive Installation (Recommended)
```bash
pip install 'lobby-ai[interactive]'
```
This adds beautiful interactive prompts with menus and multi-select options.

### Full Installation
```bash
pip install 'lobby-ai[all]'
```
Includes all features including interactive prompts and billing integrations.

### Development Installation
```bash
git clone https://github.com/franco/lobby
cd lobby
pip install -e ".[interactive]"
```

## First Time Setup

### Interactive Setup (Recommended)
```bash
lobby setup
```

This will guide you through:
1. **API Key Entry**: Secure password input for your OpenRouter API key
2. **Agent Selection**: Choose your default agent from a menu
   - `developer` - Code generation and technical tasks
   - `writer` - Content creation and documentation
   - `analyst` - Data analysis and insights
   - `researcher` - Research and information gathering
   - `strategist` - Planning and strategy
3. **Model Selection**: Pick your preferred AI model
   - 🎁 FREE models are clearly marked
   - 💰 Paid models show cost indicators
   - 💎 Premium models for best quality
4. **Secure Storage**: Your API key is stored:
   - macOS: In the system Keychain (most secure)
   - Linux/Windows: Encrypted file with password protection

### Non-Interactive Setup (CI/Automation)
```bash
lobby --no-interactive setup \
  --api-key YOUR_OPENROUTER_KEY \
  --agent developer \
  --model auto
```

### Environment Variables
You can also set your API key via environment:
```bash
export OPENROUTER_API_KEY='sk-or-...'
```

## Using LOBBY

### Basic Request (Interactive)
```bash
lobby request "Build a Python web scraper for Hacker News"
```

In interactive mode, you'll be prompted for:
- Agent specialization (if not specified)
- AI model selection
- Tools to enable (optional)
- Advanced options (temperature, cost limits)

### Quick Request (Non-Interactive)
```bash
# Use all defaults
lobby req "Write unit tests for user.py"

# Specify options via flags
lobby --no-interactive request "Analyze sales data" \
  --agent analyst \
  --model "google/gemini-flash-1.5" \
  --tools "database-query,file-operations" \
  --temperature 0.5 \
  --max-cost 0.50
```

### Available Tools
- `web-search` - Search the web for information
- `code-execution` - Run code snippets
- `file-operations` - Read/write files
- `database-query` - Query databases
- `api-calls` - Make API requests
- `git-operations` - Git commands

## Pattern Management

Patterns are reusable task templates that save time for common requests.

### List Available Patterns
```bash
lobby patterns list
# or just
lobby patterns
```

### Use a Pattern
```bash
lobby patterns run "Code Review"
```
You'll be prompted to fill in template variables like:
- File path to review
- Specific focus areas
- etc.

### Create New Pattern
```bash
lobby patterns new
```

Interactive prompts will guide you through:
1. **Pattern Name**: e.g., "Database Migration"
2. **Category**: development, content, analysis, etc.
3. **Description**: What this pattern does
4. **Agent**: Which agent to use by default
5. **Model**: Preferred AI model
6. **Tools**: Which tools to enable
7. **Template**: The task template with {variables}
   ```
   Example: "Migrate database from {source_db} to {target_db} 
   including {tables} with proper error handling"
   ```
8. **Variables**: Description for each variable found

### Edit Pattern
```bash
lobby patterns edit "Blog Post"
```
Select which fields to modify from a checklist.

### Delete Pattern
```bash
lobby patterns delete "Old Pattern"
```

## Advanced Features

### Check Service Status
```bash
lobby status
```
Shows:
- Available AI providers
- Connection status
- Active providers count

### View Configuration
```bash
lobby config
```
Displays current configuration and API key status.

### MCP Server Mode
For integration with Claude CLI, Cursor, etc.:
```bash
lobby mcp
```
This starts LOBBY as an MCP server that other tools can connect to.

### Non-Interactive Mode
For scripts and automation:
```bash
# Force non-interactive
lobby --no-interactive request "task"

# Or via environment
CI=1 lobby request "task"
DOORMAN_CI=1 lobby request "task"
```

### Dry Run Mode
Preview what would be executed without running:
```bash
lobby request "Build API client" --dry-run
```

## Security Features

### API Key Storage

#### macOS (Keychain)
Your API key is stored in the macOS Keychain:
- Encrypted by the system
- No password needed for retrieval
- Accessible only by LOBBY

#### Linux/Windows (Encrypted File)
Your API key is stored in an encrypted file:
- Location: `~/.config/lobby/.secure_storage`
- Protected with your password
- Uses PBKDF2 for key derivation
- File permissions set to user-only (600)

### Secret Redaction
All logs automatically redact:
- API keys
- Passwords
- Tokens
- Any string matching secret patterns

### Retrieve Stored API Key
The CLI automatically tries to retrieve your stored API key:
1. First checks environment variable
2. Then checks secure storage (Keychain/encrypted file)
3. Prompts if not found (in interactive mode)

## Troubleshooting

### "API key required for full service"
**Solution**: Run `lobby setup` to configure your API key, or set the `OPENROUTER_API_KEY` environment variable.

### "Pattern not found"
**Solution**: Check exact pattern name with `lobby patterns list`. Pattern names are case-insensitive but must match.

### Interactive prompts not working
**Solutions**:
1. Install with interactive extras: `pip install 'lobby-ai[interactive]'`
2. Check if you're in a TTY environment: `python -c "import sys; print(sys.stdin.isatty())"`
3. Disable CI mode if set: `unset CI; unset DOORMAN_CI`

### Can't store API key securely
**macOS**: Ensure you have Keychain access permissions.
**Linux/Windows**: Install cryptography: `pip install cryptography`

### MCP server won't start
Ensure MCP is installed: `pip install mcp`

### Import errors
Reinstall with all dependencies:
```bash
pip uninstall lobby-ai
pip install --upgrade 'lobby-ai[all]'
```

## Command Reference

### Global Options
- `--interactive` / `--no-interactive` - Control interactive mode
- `--help` / `-h` - Show help

### Commands
- `setup` - Initial configuration wizard
- `request` / `req` - Submit a task to AI
- `patterns` - Manage task patterns
  - `list` - Show all patterns
  - `new` - Create new pattern
  - `run <name>` - Execute a pattern
  - `edit <name>` - Modify a pattern
  - `delete <name>` - Remove a pattern
- `status` - Check service status
- `config` - Show configuration
- `mcp` - Start MCP server

### Request Options
- `--agent` / `-a` - Agent to use
- `--model` / `-m` - AI model
- `--temperature` / `-t` - Creativity (0-1)
- `--max-cost` - Maximum cost in USD
- `--tools` - Comma-separated tools
- `--dry-run` - Preview without executing

## Tips & Best Practices

1. **Use Patterns**: Create patterns for tasks you do frequently
2. **Free Models First**: LOBBY prioritizes free models when possible
3. **Secure Storage**: Always use `lobby setup` to store API keys securely
4. **Non-Interactive for Scripts**: Use `--no-interactive` in scripts
5. **Check Status**: Run `lobby status` to verify service availability
6. **Cost Control**: Set `--max-cost` to limit spending

## Support

- GitHub Issues: [github.com/franco/lobby/issues](https://github.com/franco/lobby/issues)
- Documentation: This guide and README.md
- Email: support@lobby.directory

---

Made with ❤️ in NYC - Your AI concierge is ready to serve!