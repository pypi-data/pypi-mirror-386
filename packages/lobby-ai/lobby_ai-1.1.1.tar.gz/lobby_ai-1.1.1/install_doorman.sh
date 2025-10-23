#!/bin/bash

# DOORMAN Installation Script
# Production-Grade AI Orchestration CLI

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  DOORMAN.EXE v2.0 ▮▮▮ INSTALLER ▮▮▮        ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Production-Grade AI Orchestration         ║"
echo "║  FREE OpenRouter Models + Smart Routing     ║"
echo "╚══════════════════════════════════════════════╝"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "doorman_simple.py" ]; then
    echo "❌ Please run this from the doorman directory"
    exit 1
fi

echo "🔍 Installing dependencies..."

# Install required packages
pip3 install typer rich httpx

echo "✅ Dependencies installed!"

# Check for OpenRouter API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo
    echo "⚠️  OPENROUTER_API_KEY not set!"
    echo
    echo "To use FREE models, get your API key:"
    echo "1. Visit: https://openrouter.ai/"
    echo "2. Sign up and get your API key"
    echo "3. Export it:"
    echo "   export OPENROUTER_API_KEY='your-key-here'"
    echo
    echo "Or add to your ~/.zshrc:"
    echo "   echo 'export OPENROUTER_API_KEY=\"your-key\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo
fi

# Create executable
chmod +x doorman_simple.py

# Test installation
echo
echo "🧪 Testing installation..."
echo

python3 doorman_simple.py demo

echo
echo "╔══════════════════════════════════════════════╗"
echo "║                 🎉 SUCCESS! 🎉               ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Doorman is now installed and ready to use  ║"
echo "╚══════════════════════════════════════════════╝"
echo
echo "📖 Usage Examples:"
echo
echo "  # Quick demo"
echo "  python3 doorman_simple.py demo"
echo
echo "  # Create plans for any task"
echo "  python3 doorman_simple.py plan 'write a bash script'"
echo "  python3 doorman_simple.py plan 'create a blog post about AI'"
echo "  python3 doorman_simple.py plan 'analyze data trends'"
echo
echo "  # Check provider status"
echo "  python3 doorman_simple.py providers"
echo
echo "  # See routing without API calls"
echo "  python3 doorman_simple.py plan 'your task' --dry-run"
echo
echo "💰 FREE Models Available:"
echo "  • agentica-org/deepcoder-14b-preview:free (coding)"
echo "  • meta-llama/llama-3.1-8b-instruct:free (general)"
echo "  • microsoft/wizardlm-2-8x22b:free (reasoning)"
echo
echo "🔗 Set your API key: export OPENROUTER_API_KEY='your-key'"
echo "🎯 Start with: python3 doorman_simple.py plan 'your task here'"