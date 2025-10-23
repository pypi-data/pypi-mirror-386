#!/usr/bin/env python3
"""
Main entry point for LOBBY CLI.
Provides helpful error messages for missing dependencies.
"""

import sys


def main():
    """Main entry point with dependency checking."""
    try:
        from lobby.cli import main as cli_main

        cli_main()
    except ImportError as e:
        print(f"Error: Missing dependencies - {e}")
        print("\nTo fix this, try:")

        if "InquirerPy" in str(e) or "questionary" in str(e):
            print("  pip install 'lobby-ai[interactive]'  # For interactive prompts")
        elif "cryptography" in str(e):
            print("  pip install cryptography  # For secure storage")
        elif "mcp" in str(e):
            print("  pip install mcp  # For MCP server functionality")
        else:
            print("  pip install --upgrade 'lobby-ai[all]'  # Install all dependencies")

        print("\nFor minimal installation:")
        print("  pip install lobby-ai")
        print("\nFor full documentation, see USER_GUIDE.md")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("\nFor help, run: lobby --help")
        print("For documentation, see USER_GUIDE.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
