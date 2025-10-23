# 🏢 LOBBY - AI Concierge for CLI Tools

<!-- mcp-name: io.github.devopsfranco/lobby -->

**Multiply your existing CLI tools with intelligent AI orchestration**

LOBBY is an AI concierge service that works **with** your existing CLI tools (Claude, Gemini, Cursor, etc.) to provide intelligent task routing and execution planning. It doesn't replace your tools - it makes them smarter.

## ⚡ Quick Install

```bash
# Node (npx wrapper)
npx lobby-ai --help

# Python (user local)
pip install lobby-ai

# Isolated, recommended for CLIs
pipx install lobby-ai
# or
uvx lobby-ai --help
```

That's it! 🎉

## 🚀 What is LOBBY?

LOBBY multiplies your CLI tools by providing:

1. **🎯 Intelligent Routing** - Optimal model selection for each task type
2. **💰 Cost Optimization** - Prefers free models, shows real costs
3. **🔌 MCP Server** - Works with Claude CLI, Gemini CLI, Cursor, any MCP tool
4. **🏢 NYC Concierge** - Professional service that elevates your workflow

## 🛠️ How It Works

LOBBY runs as an **MCP (Model Context Protocol) server** that your existing CLI tools can connect to:

- **Claude CLI** → calls LOBBY for smart orchestration
- **Gemini CLI** → calls LOBBY for cost optimization  
- **Cursor IDE** → calls LOBBY for task routing
- **Any MCP tool** → gets LOBBY's AI concierge services

## 🎯 What You Get

### **Intelligent Routing**
- **Coding tasks** → DeepCoder (free) or Claude-3.5 Sonnet
- **Writing tasks** → GPT-4 or Claude-3 Opus  
- **Analysis tasks** → Gemini 1.5 Pro or Llama-3.1
- **Creative tasks** → DALL-E + GPT-4 or Midjourney API

### **Cost Optimization** 
- Prefers **FREE models** (agentica-org/deepcoder:free, etc.)
- Routes to cheapest option that meets quality requirements
- Shows real-time cost estimates
- Usage tracking and billing

### **Professional Execution Plans**
- Multi-step actionable plans with shell commands
- Quality assurance checkpoints
- Expected deliverables and outcomes

## 🚀 Setup (30 seconds)

```bash
# 1. Install with basic features
pip install lobby-ai

# Or install with interactive prompts (recommended)
pip install 'lobby-ai[interactive]'

# 2. Configure (auto-detects Claude, Gemini, etc.)
lobby setup

# 3. Start using through your existing CLI tools!
```

### ✨ Interactive Setup Wizard

With the `[interactive]` extras installed, you get a beautiful setup wizard:

```bash
lobby setup
# ✅ Interactive API key entry (secure password input)
# ✅ Choose default agent from menu (developer, writer, analyst, etc.)
# ✅ Select preferred AI model with cost indicators
# ✅ Configure tools and preferences
```

## 📋 Usage Examples

### Interactive Request Mode
```bash
# Interactive mode with menus and selections
lobby request "Build a web scraper"
# ✅ Select agent specialization
# ✅ Choose AI model (with FREE options highlighted)
# ✅ Pick tools to enable
# ✅ Configure advanced options

# Non-interactive for automation
lobby --no-interactive request "Build a web scraper" \
  --agent developer --model auto --tools code-execution,web-search
```

### Pattern Management
```bash
# Create reusable task patterns
lobby patterns new
# ✅ Interactive pattern builder with variables
# ✅ Save templates for common tasks

# Run saved patterns
lobby patterns run "Code Review"
# ✅ Fill in template variables
# ✅ Execute with saved preferences

# List all patterns
lobby patterns list
```

### In Claude CLI:
```bash
claude> Use LOBBY to build a Python web scraper for Hacker News
claude> Ask LOBBY to analyze my GitHub repo structure
claude> Get LOBBY to write a technical blog post about AI agents
```

### In Gemini CLI:
```bash
gemini> Use LOBBY orchestration to create a React dashboard
gemini> Have LOBBY optimize my database queries
```

## 🏢 MCP Tools Available

Once installed, these tools are available to all your CLI clients:

- **`orchestrate_task`** - Full AI task orchestration with optimal routing
- **`analyze_routing`** - Preview which models would be selected  
- **`check_usage`** - View your usage and billing status

## 💳 Pricing

- **Free**: 10 orchestrations per day
- **After free tier**: $0.01 per orchestration
- **Professional**: $29/month (2,500 orchestrations)
- **Enterprise**: $99/month (unlimited)

*Note: You still pay model providers directly (OpenRouter, Anthropic, etc.). LOBBY charges only for the orchestration service.*

## ⚙️ Requirements

- Python 3.8+
- An OpenRouter API key (get free credits at [openrouter.ai](https://openrouter.ai))
- At least one MCP-compatible CLI tool:
  - [Claude CLI](https://claude.ai/cli) 
  - [Gemini CLI](https://ai.google.dev/cli)
  - [Cursor IDE](https://cursor.sh)
  - Any other MCP-compatible tool

## 🎯 Philosophy

**LOBBY multiplies your existing tools instead of replacing them.**

We believe the future is multi-model, multi-provider. Instead of being locked into one AI company's tools, LOBBY lets you:

✅ **Keep using** Claude CLI, Gemini CLI, Cursor, etc.  
✅ **Add intelligence** through optimal model routing  
✅ **Save money** with cost optimization and free models  
✅ **Get better results** with task-specific model selection  

## 📚 Further docs

- Build from source (pyproject):
  - python -m build  # requires build
  - pip install -U build && python -m build
  - pip install dist/*.whl
- Pre-commit hooks: pre-commit install
- Lint/format: ruff format . && ruff check . --fix

- See USER_GUIDE.md for a complete command reference and user journey walkthrough
- See IMPLEMENTATION_SUMMARY.md for architecture details and testing

## 📚 Support

- **Website**: [lobby.directory](https://lobby.directory)
- **GitHub Issues**: [github.com/franco/lobby](https://github.com/franco/lobby)
- **Email Support**: support@lobby.directory

## License

MIT License - see [LICENSE](LICENSE) file.

---

**Made with ❤️ in NYC** - Your AI concierge is ready to serve!
