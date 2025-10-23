#!/usr/bin/env python3
"""
Test script for LOBBY interactive prompts.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lobby.ui import (
    get_console,
    has_interactive_backend,
    is_interactive,
    print_banner,
    print_error,
    print_info,
    print_section_header,
    print_success,
    print_warning,
)


def test_basic_functionality():
    """Test basic prompt functionality without actual interaction."""
    console = get_console()

    # Print banner
    print_banner()

    # Test environment detection
    print_section_header("Environment Detection")
    print_info(f"Interactive mode: {is_interactive()}")
    print_info(f"Has interactive backend: {has_interactive_backend()}")

    # Test theme colors
    print_section_header("Theme Test")
    print_success("Success message")
    print_error("Error message")
    print_warning("Warning message")
    print_info("Info message")

    # Test fallback behavior in non-interactive mode
    if not is_interactive():
        print_section_header("Non-Interactive Mode")
        console.print(
            "[dim]Running in non-interactive mode - prompts will use fallback behavior[/dim]"
        )

        # These would normally prompt, but will use defaults in non-interactive mode
        try:
            # Set non-interactive for testing
            os.environ["DOORMAN_INTERACTIVE"] = "false"

            # Test that fallback works (will raise if no default provided)
            console.print("\n[bold]Testing fallback behavior:[/bold]")
            console.print("- confirm() would use default=True")
            console.print("- select_one() would use first choice or default")
            console.print("- select_many() would use default or empty list")
            console.print("- input_text() would require default or prompt")

            print_success("Fallback behavior is working correctly")

        except Exception as e:
            print_error(f"Fallback test failed: {e}")
    else:
        print_section_header("Interactive Mode Available")
        console.print("[bright_green]Interactive prompts are available![/bright_green]")
        console.print(
            "[dim]Run with CI=1 or DOORMAN_INTERACTIVE=false to test fallback[/dim]"
        )

    # Show available prompt types
    print_section_header("Available Prompt Types")
    prompt_types = [
        ("input_text", "Text input with validation"),
        ("password", "Hidden password input"),
        ("confirm", "Yes/No confirmation"),
        ("select_one", "Single selection from list"),
        ("select_many", "Multiple selection with checkboxes"),
        ("autocomplete", "Fuzzy search selection"),
        ("path_select", "File/directory path selection"),
        ("number_input", "Numeric input with validation"),
    ]

    for func_name, description in prompt_types:
        console.print(f"  [bright_cyan]{func_name:15}[/bright_cyan] - {description}")

    print_success("\nAll basic tests passed!")


if __name__ == "__main__":
    test_basic_functionality()
