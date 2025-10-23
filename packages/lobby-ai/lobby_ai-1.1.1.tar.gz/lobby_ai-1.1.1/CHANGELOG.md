# Changelog

All notable changes to LOBBY AI Concierge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-10-22

### Changed
- Codebase cleanup for stability and polish
- Use pathlib for config paths in lobby/cli.py
- Harden config file permissions to 0600

### Fixed
- Linting issues (SIM102 nested ifs, import reordering, unused imports)
- Removed deprecated lobby/mcp_server_broken.py implementation; now a clear placeholder
- Ensured MCP server remains non-interactive and import-safe

### Misc
- Verified CLI runtime (`status`, `request --dry-run`, `req --preview`) without configured providers

## [1.1.0] - 2024-01-18

### Added
- **Interactive Prompts System** - Beautiful Inquirer-style prompts with Typer compatibility
  - Optional installation via `pip install lobby-ai[interactive]`
  - InquirerPy and questionary support with automatic fallback to Typer
  - Password inputs, select menus, multi-select checkboxes, autocomplete
  - Path selection with validation
  - Number inputs with range validation
  
- **Interactive Setup Wizard** 
  - Secure API key entry with password masking
  - Agent selection from menu (developer, writer, analyst, etc.)
  - Model selection with cost indicators (FREE models highlighted)
  - Tool configuration with multi-select
  
- **Pattern Management System**
  - Create reusable task patterns with templates and variables
  - Interactive pattern builder with variable extraction
  - Pattern categories and search functionality
  - Usage tracking and most-used patterns
  - SQLite persistence in `~/.config/lobby/patterns.db`
  
- **Enhanced Request Command**
  - Interactive agent and model selection
  - Tool selection with checkboxes
  - Advanced options (temperature, max cost)
  - Preview and confirmation before execution
  
- **NYC Professional Theme**
  - Consistent styling across Rich console and prompts
  - Bright cyan headers, gold accents
  - Professional color palette
  
- **Non-Interactive Mode**
  - Global `--interactive/--no-interactive` flag
  - Automatic detection of CI/TTY environment
  - Full functionality via CLI arguments
  - Graceful fallback when interactive packages not installed

### Changed
- Refactored setup command to use interactive prompts
- Updated package structure with `lobby/ui/` module
- Enhanced MCP server with non-interactive guards
- Improved error messages and user guidance

### Technical
- Added comprehensive test suite for prompts
- Environment detection (CI, DOORMAN_CI, TTY)
- Fallback chain: InquirerPy → questionary → Typer
- Optional dependencies via `extras_require`

### Migration Guide
For existing users:
1. Update: `pip install --upgrade lobby-ai[interactive]`
2. Run new setup: `lobby setup`
3. Try patterns: `lobby patterns list`
4. Interactive requests: `lobby request "your task"`

For automation/CI:
- Use `--no-interactive` flag: `lobby --no-interactive request "task" --agent developer`
- Set `CI=1` or `DOORMAN_CI=1` environment variable
- All commands work with CLI arguments

## [1.0.0] - 2024-01-15

### Added
- Initial release of LOBBY AI Concierge
- MCP server implementation
- Intelligent task routing
- Cost optimization with free model preference  
- OpenRouter integration
- Basic CLI with Typer
- Usage tracking and billing system
- Claude CLI, Gemini CLI, Cursor compatibility
- NYC concierge theming