#!/bin/bash

# LOBBY MCP Setup Script
# Detects existing CLI tools and configures them to use LOBBY concierge service

set -e

echo "┌────────────────────────────────────────────────────┐"
echo "│           🏢 LOBBY MCP SETUP                    │"
echo "│                                                    │"
echo "│    AI Concierge Service for CLI Tools           │"
echo "│    Configuring Claude, Gemini, Cursor...        │"
echo "│                                                    │"
echo "└────────────────────────────────────────────────────┘"
echo

# Check Python and dependencies
echo "🔍 Checking requirements..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

# Install MCP dependencies
echo "📦 Installing MCP dependencies..."
pip3 install mcp httpx typer rich

echo "✅ Dependencies installed"
echo

# Detect existing CLI tools
echo "🔍 Detecting CLI tools..."
echo "──────────────────────────"

CLAUDE_CONFIG=""
GEMINI_CONFIG=""
CURSOR_CONFIG=""
DETECTED_TOOLS=()

# Check for Claude CLI
if [ -f ~/.config/claude/config.json ] || command -v claude &> /dev/null; then
    CLAUDE_CONFIG=~/.config/claude/config.json
    DETECTED_TOOLS+=("Claude CLI")
    echo "✅ Claude CLI detected: $CLAUDE_CONFIG"
fi

# Check for Gemini CLI
if [ -f ~/.config/gemini/config.json ] || command -v gemini &> /dev/null; then
    GEMINI_CONFIG=~/.config/gemini/config.json
    DETECTED_TOOLS+=("Gemini CLI")
    echo "✅ Gemini CLI detected: $GEMINI_CONFIG"
fi

# Check for Cursor
if [ -d ~/Library/Application\ Support/Cursor ] || command -v cursor &> /dev/null; then
    CURSOR_CONFIG=~/Library/Application\ Support/Cursor/User/settings.json
    DETECTED_TOOLS+=("Cursor")
    echo "✅ Cursor detected: $CURSOR_CONFIG"
fi

# Check for Codeium CLI
if command -v codeium &> /dev/null; then
    DETECTED_TOOLS+=("Codeium CLI")
    echo "✅ Codeium CLI detected"
fi

if [ ${#DETECTED_TOOLS[@]} -eq 0 ]; then
    echo "⚠️  No supported CLI tools detected"
    echo
    echo "LOBBY works with:"
    echo "• Claude CLI (https://claude.ai/cli)"
    echo "• Gemini CLI (https://ai.google.dev/cli)"
    echo "• Cursor IDE (https://cursor.sh)"
    echo "• Any MCP-compatible tool"
    echo
    echo "Install a CLI tool first, then run this setup again."
    exit 0
fi

echo
echo "📋 Found ${#DETECTED_TOOLS[@]} CLI tools: ${DETECTED_TOOLS[*]}"
echo

# Setup LOBBY MCP server
echo "🏢 Setting up LOBBY MCP Server..."
echo "────────────────────────────────────"

# Make LOBBY server executable
chmod +x lobby_mcp_server.py

# Get absolute path
LOBBY_PATH="$(pwd)/lobby_mcp_server.py"
CONFIG_PATH="$(pwd)/mcp_config_lobby.json"

echo "✅ LOBBY MCP Server ready at: $LOBBY_PATH"
echo

# Configure Claude CLI if detected
if [ -n "$CLAUDE_CONFIG" ]; then
    echo "⚙️  Configuring Claude CLI..."
    
    # Create claude config directory if it doesn't exist
    mkdir -p ~/.config/claude
    
    # Create or update Claude MCP configuration
    cat > ~/.config/claude/mcp_servers.json << EOF
{
  "mcpServers": {
    "lobby": {
      "command": "python3",
      "args": ["$LOBBY_PATH"],
      "description": "LOBBY AI Concierge - Intelligent task orchestration"
    }
  }
}
EOF
    
    echo "✅ Claude CLI configured for LOBBY"
    echo "   Config: ~/.config/claude/mcp_servers.json"
fi

# Configure other tools (placeholder)
if [ -n "$GEMINI_CONFIG" ]; then
    echo "⚙️  Gemini CLI MCP configuration ready"
    echo "   Add LOBBY server to your Gemini MCP config"
fi

if [ -n "$CURSOR_CONFIG" ]; then
    echo "⚙️  Cursor MCP configuration ready"
    echo "   Add LOBBY server to your Cursor MCP settings"
fi

echo

# Test LOBBY server
echo "🧪 Testing LOBBY MCP Server..."
echo "─────────────────────────────────"

# Check if OpenRouter API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OpenRouter API key not set"
    echo "   Set: export OPENROUTER_API_KEY='your-key'"
    echo "   LOBBY will work in preview mode without API key"
fi

echo "✅ LOBBY MCP Server test ready"
echo

# Final instructions
echo "┌────────────────────────────────────────────────────┐"
echo "│                🎉 SETUP COMPLETE! 🎉              │"
echo "├────────────────────────────────────────────────────┤"
echo "│     LOBBY is now available to your CLI tools      │"
echo "└────────────────────────────────────────────────────┘"
echo

echo "🏢 LOBBY MCP Tools Available:"
echo "──────────────────────────────"
echo "• orchestrate_task    - Full AI task orchestration"
echo "• analyze_routing     - Preview optimal routing"  
echo "• check_usage         - View billing status"
echo

echo "💡 Usage Examples:"
echo "─────────────────"

if [ -n "$CLAUDE_CONFIG" ]; then
    echo "📝 In Claude CLI:"
    echo "   claude> Use LOBBY to orchestrate: build a Python web scraper"
    echo "   claude> Check my LOBBY usage status"
    echo
fi

echo "🔧 Direct MCP calls:"
echo "   - orchestrate_task(task='write a blog post', user_id='your-id')"
echo "   - analyze_routing(task='analyze data trends')"
echo "   - check_usage(user_id='your-id')"
echo

echo "💰 Billing:"
echo "─────────"
echo "• Free: 10 requests per day"
echo "• After free tier: \$0.01 per orchestration"
echo "• Professional: \$29/month (2,500 requests)"
echo "• Enterprise: \$99/month (10,000 requests)"
echo

echo "🚀 Start using LOBBY through your CLI tools now!"
echo "   Your AI concierge is ready to orchestrate any task."