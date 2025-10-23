# Doorman - Production Ready AI Orchestration CLI

## 🚀 Overview

Doorman is a production-ready AI orchestration CLI that intelligently routes tasks to the optimal AI provider based on task type, cost, and performance. It transforms natural language requests into executable shell scripts.

## ✅ Production Ready Status

✅ **Core Functionality Verified**
- CLI commands work correctly
- Plan generation produces valid shell scripts
- Configuration management is functional
- Provider routing works as expected

✅ **Quality Assurance**
- All core functionality tests pass
- Error handling is robust
- User experience is smooth and intuitive

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/franco/doorman.git
cd doorman

# Install dependencies
pip install -r requirements.txt

# Set your OpenRouter API key
export OPENROUTER_API_KEY='your-openrouter-api-key'
```

## 🎯 Key Features

### 1. Intelligent Task Planning
```bash
# Generate a plan for any task
doorman plan "create a python web scraper for news articles"

# Generate just the shell script
doorman plan "setup a react project" --script-only

# Save script to file
doorman plan "deploy to vercel" --script-only --output deploy.sh
```

### 2. Multi-Provider Routing
```bash
# Check available providers
doorman providers list

# Test routing for a task
doorman providers route "analyze sales data"
```

### 3. Configuration Management
```bash
# Check configuration status
doorman config doctor

# Set configuration values
doorman config set default_model openai/gpt-4-turbo
doorman config set max_cost_per_plan 2.0
```

### 4. Agent Selection
```bash
# View available AI agents
doorman fighters
```

## 🔧 Configuration

### Required Environment Variables
```bash
# OpenRouter API key (required for AI functionality)
export OPENROUTER_API_KEY='your-openrouter-api-key'

# Optional: Customize behavior
export DOORMAN_MODEL='openai/gpt-4-turbo'
export DOORMAN_VERBOSE='true'
```

### Configuration File
Doorman automatically creates a configuration file at `~/.config/doorman/config.json`:
```json
{
  "openrouter_api_key": "your-api-key-here",
  "default_model": "openai/gpt-3.5-turbo",
  "max_cost_per_plan": 1.0
}
```

## 🎮 Usage Examples

### Development Tasks
```bash
# Create a new project
doorman plan "create a new react app called my-dashboard"

# Set up development environment
doorman plan "install nodejs and python on ubuntu"

# Debug code issues
doorman plan "fix this python memory leak issue"
```

### System Administration
```bash
# Server setup
doorman plan "install nginx and configure ssl on ubuntu"

# Backup scripts
doorman plan "create a backup script for postgresql database"

# Monitoring
doorman plan "set up prometheus monitoring for docker containers"
```

### Creative & Business Tasks
```bash
# Content creation
doorman plan "write a blog post about AI orchestration"

# Data analysis
doorman plan "analyze customer data from csv file"

# Report generation
doorman plan "create a monthly sales report from json data"
```

## 🛡️ Safety Features

### Command Safety Levels
- **Safe**: Read-only operations, no side effects
- **Moderate**: File operations, installations
- **Dangerous**: System modifications, requires confirmation

### Automatic Safety Checks
- All dangerous commands require explicit confirmation
- Clear warnings for privileged operations
- Estimated execution time and resource usage

## 📊 Billing & Usage

### Usage Tracking
```bash
# Check usage (if Clerk integration is configured)
doorman billing status
```

### Cost Management
- Prefers free models when available
- Shows estimated costs before execution
- Configurable cost limits

## 🤝 Integration

### MCP (Model Context Protocol) Support
Doorman works as both an MCP server and client:
```bash
# Run as MCP server
doorman mcp-server

# Discover MCP tools
doorman mcp-client discover
```

### Plugin System
Extend functionality with custom plugins:
```bash
# List available plugins
doorman plugins list

# Create a new plugin
doorman plugins create my-tool tool
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Recognized**
   ```bash
   # Check configuration
   doorman config doctor
   
   # Set API key
   export OPENROUTER_API_KEY='your-key'
   ```

2. **Generated Scripts Not Working**
   ```bash
   # Generate script only for review
   doorman plan "your task" --script-only
   
   # Manually review and modify before execution
   ```

3. **Provider Connection Issues**
   ```bash
   # Check provider status
   doorman providers list
   
   # Test API key
   doorman config doctor
   ```

## 📈 Performance

### Response Times
- Plan generation: 2-5 seconds
- Script execution: Depends on task complexity
- Provider routing: < 100ms

### Resource Usage
- Memory: < 100MB
- CPU: Minimal during planning
- Network: Only when calling AI providers

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai) for AI model access
- [SurrealDB](https://surrealdb.com) for database functionality
- [Typer](https://typer.tiangolo.com) for CLI framework
- [Rich](https://rich.readthedocs.io) for beautiful terminal output