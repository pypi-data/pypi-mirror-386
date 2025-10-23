#!/bin/bash

# LOBBY Installation Script
# NYC-style AI concierge for intelligent task orchestration

set -e

echo "┌────────────────────────────────────────────────────┐"
echo "│                                                    │"
echo "│           🏢 L O B B Y                          │"
echo "│                                                    │"
echo "│        INSTALLATION & SETUP SCRIPT              │"
echo "│        Your AI concierge awaits                 │"
echo "│                                                    │"
echo "└────────────────────────────────────────────────────┘"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "   Install Python: https://python.org/downloads/"
    exit 1
fi

echo "🔍 Installing dependencies..."

# Install required packages
pip3 install typer rich httpx sqlite3 flask flask-cors stripe

echo "✅ Dependencies installed!"
echo

# Check for OpenRouter API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "🔑 API Key Setup Required"
    echo "──────────────────────────"
    echo
    echo "To use LOBBY's AI concierge services:"
    echo "1. Visit: https://openrouter.ai/"
    echo "2. Sign up and get your API key"
    echo "3. Set your environment variable:"
    echo
    echo "   export OPENROUTER_API_KEY='your-key-here'"
    echo
    echo "4. Add to your shell profile for persistence:"
    echo "   echo 'export OPENROUTER_API_KEY=\"your-key\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo
else
    echo "✅ OpenRouter API key detected"
fi

# Make executables
chmod +x lobby.py
chmod +x lobby_billing.py

echo "🧪 Testing LOBBY installation..."
echo

# Test basic functionality
python3 lobby.py demo

echo
echo "┌────────────────────────────────────────────────────┐"
echo "│                🎉 SUCCESS! 🎉                    │"
echo "├────────────────────────────────────────────────────┤"
echo "│    LOBBY is installed and ready to serve you      │"
echo "└────────────────────────────────────────────────────┘"
echo
echo "🏢 LOBBY Concierge Commands:"
echo "───────────────────────────────"
echo
echo "  📝 Submit a request:"
echo "     python3 lobby.py request 'build a web scraper'"
echo "     python3 lobby.py request 'write a business plan'"
echo "     python3 lobby.py request 'analyze sales data'"
echo
echo "  👀 Preview without execution:"
echo "     python3 lobby.py request 'your task' --preview"
echo
echo "  📊 Check service status:"
echo "     python3 lobby.py status"
echo
echo "  ⚙️  View configuration:"
echo "     python3 lobby.py config"
echo
echo "  🎭 Experience the demo:"
echo "     python3 lobby.py demo"
echo
echo "  📖 Get help:"
echo "     python3 lobby.py help"
echo
echo "💡 Features:"
echo "────────────"
echo "  • FREE AI models (complimentary service)"
echo "  • Intelligent task routing & classification"
echo "  • Professional execution plans"
echo "  • NYC-style concierge experience"
echo "  • Real-time usage tracking"
echo
echo "🚀 Start with: python3 lobby.py request 'your task here'"
echo
echo "📋 Billing Services (Optional):"
echo "─────────────────────────────────"
echo "  • Start billing API: python3 lobby_billing.py"
echo "  • Professional: \$29/month (2,500 requests)"
echo "  • Enterprise: \$99/month (10,000 requests)"
echo
echo "Welcome to LOBBY - your AI concierge service!"