#!/usr/bin/env python3
"""
Complete LOBBY Installation Demo
Shows the "really, really easy" installation experience
"""

import sys


def demo_pip_install():
    """Demonstrate the complete pip install experience."""
    print("🏢 LOBBY AI - Complete Installation Demo")
    print("=" * 50)
    print()

    print("Step 1: Install LOBBY")
    print("$ pip install lobby-ai")
    print("✅ Successfully installed lobby-ai-1.0.0")
    print("✅ Commands available: lobby, lobby-mcp")
    print()

    print("Step 2: Check what we got")
    print("$ lobby")
    print()

    # Import and run the CLI to show the banner
    try:
        from lobby.cli import print_banner

        print_banner()

        print("🎯 [bold]Quick Start:[/bold]")
        print("   lobby setup     - Configure with your CLI tools (30 seconds)")
        print("   lobby request 'task' - Get AI orchestration for any task")
        print("   lobby status    - Check service availability")
        print()
        print("💡 Get started: lobby setup")
        print()

    except Exception as e:
        print(f"Error running CLI: {e}")
        return False

    print("Step 3: Configure with existing CLI tools")
    print("$ lobby setup")
    print("✅ OpenRouter API key detected")
    print("✅ Found Claude CLI configuration")
    print("✅ Also found: Cursor")
    print("🔧 MCP integration configured for all compatible tools")
    print("🎉 Setup Complete!")
    print()

    print("Step 4: Start using through your existing tools")
    print()
    print("In Claude CLI:")
    print('  claude> "Use LOBBY to build a Python web scraper"')
    print("  🏢 LOBBY AI Concierge Service")
    print("  📋 Service Request Analysis:")
    print("  • Task Category: Development project")
    print("  • AI Provider: OPENROUTER")
    print("  • Model: agentica-org/deepcoder-14b-preview:free")
    print("  • Service Cost: Complimentary")
    print("  • Billing: Free (10 remaining)")
    print()

    print("In Cursor IDE:")
    print("  [MCP Tools Panel]")
    print("  🏢 LOBBY - orchestrate_task")
    print("  📊 LOBBY - check_usage")
    print("  🎯 LOBBY - analyze_routing")
    print()

    print("Step 5: Advanced usage (optional)")
    print("$ lobby-mcp  # Start standalone MCP server")
    print("❌ MCP dependencies not installed")
    print("Install with: pip install mcp")
    print("(Optional - only needed for advanced MCP server usage)")
    print()

    print("🎯 [bold]Summary:[/bold]")
    print("✅ Installation: 1 command (pip install lobby-ai)")
    print("✅ Setup: 1 command (lobby setup)")
    print("✅ Integration: Works with Claude CLI, Gemini CLI, Cursor")
    print("✅ Billing: Free tier (10 requests/day), then $0.01/request")
    print("✅ Models: Intelligent routing, prefers FREE models")
    print("✅ Website: https://lobby.directory")
    print()

    print("🚀 [bold]Ready to multiply your CLI tools with AI![/bold]")

    return True


if __name__ == "__main__":
    success = demo_pip_install()
    if success:
        print("\n🎉 Demo completed successfully!")
        print("   This is how easy LOBBY installation will be.")
    else:
        print("\n❌ Demo failed")
        sys.exit(1)
