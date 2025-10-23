"""
NYC Professional theme for LOBBY CLI.
Provides consistent styling for both Rich console and interactive prompts.
"""

from typing import Optional

from rich.console import Console
from rich.theme import Theme

# NYC Professional color palette
COLORS = {
    "primary": "#00FFFF",  # Bright cyan
    "secondary": "#87CEEB",  # Sky blue
    "accent": "#FFD700",  # Gold
    "success": "#00FF00",  # Bright green
    "warning": "#FFA500",  # Orange
    "danger": "#FF4444",  # Red
    "muted": "#808080",  # Gray
    "bright_white": "#FFFFFF",
    "dim": "#606060",
    "background": "#1E1E1E",  # Dark background
    "border": "#444444",  # Border gray
}

# Rich theme definition
NYC_THEME = Theme(
    {
        "primary": COLORS["primary"],
        "secondary": COLORS["secondary"],
        "accent": COLORS["accent"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
        "muted": COLORS["muted"],
        "dim": COLORS["dim"],
        "bright_white": COLORS["bright_white"],
        "bright_cyan": COLORS["primary"],
        "bright_yellow": COLORS["accent"],
        "bright_green": COLORS["success"],
        "neon_cyan": f"bold {COLORS['primary']}",
        "neon_green": f"bold {COLORS['success']}",
    }
)

# Singleton console instance
_console: Optional[Console] = None


def get_console() -> Console:
    """Get or create the themed Rich console."""
    global _console
    if _console is None:
        _console = Console(theme=NYC_THEME)
    return _console


def get_inquirer_style() -> dict:
    """
    Get InquirerPy/prompt_toolkit style dictionary.
    Returns a style configuration for consistent theming.
    """
    return {
        # InquirerPy specific styles
        "questionmark": f"fg:{COLORS['primary']} bold",
        "question": f"fg:{COLORS['bright_white']} bold",
        "answer": f"fg:{COLORS['accent']} bold",
        "pointer": f"fg:{COLORS['primary']} bold",
        "highlighted": f"fg:{COLORS['primary']} bold",
        "selected": f"fg:{COLORS['success']}",
        "separator": f"fg:{COLORS['border']}",
        "instruction": f"fg:{COLORS['muted']}",
        "text": f"fg:{COLORS['bright_white']}",
        "disabled": f"fg:{COLORS['dim']}",
        "checkbox": f"fg:{COLORS['primary']}",
        "checkbox-checked": f"fg:{COLORS['success']}",
        "checkbox-selected": f"fg:{COLORS['primary']} bold",
        "radio": f"fg:{COLORS['primary']}",
        "radio-checked": f"fg:{COLORS['success']}",
        "radio-selected": f"fg:{COLORS['primary']} bold",
        # Prompt toolkit styles
        "bottom-toolbar": f"bg:{COLORS['background']} fg:{COLORS['muted']}",
        "bottom-toolbar.text": f"fg:{COLORS['muted']}",
        "dialog": f"bg:{COLORS['background']}",
        "dialog.body": f"bg:{COLORS['background']} fg:{COLORS['bright_white']}",
        "dialog frame.label": f"fg:{COLORS['primary']} bold",
        "dialog.shadow": "bg:#000000",
        # Validation and error styles
        "validation-toolbar": f"bg:{COLORS['danger']} fg:{COLORS['bright_white']} bold",
        "error": f"fg:{COLORS['danger']} bold",
        "warning": f"fg:{COLORS['warning']}",
        "success": f"fg:{COLORS['success']}",
    }


def get_questionary_style() -> list:
    """
    Get questionary style list.
    Returns a style configuration for questionary prompts.
    """
    from questionary import Style

    return Style(
        [
            ("qmark", f"fg:{COLORS['primary']} bold"),  # ? mark
            ("question", f"fg:{COLORS['bright_white']} bold"),  # Question text
            ("answer", f"fg:{COLORS['accent']} bold"),  # User answer
            ("pointer", f"fg:{COLORS['primary']} bold"),  # Pointer for selections
            ("highlighted", f"fg:{COLORS['primary']} bold"),  # Highlighted option
            ("selected", f"fg:{COLORS['success']}"),  # Selected items
            ("separator", f"fg:{COLORS['border']}"),  # Separator lines
            ("instruction", f"fg:{COLORS['muted']}"),  # Instructions
            ("text", f"fg:{COLORS['bright_white']}"),  # Regular text
            ("disabled", f"fg:{COLORS['dim']} italic"),  # Disabled options
        ]
    )


def print_banner():
    """Print the LOBBY banner with NYC elegance."""
    console = get_console()

    banner_lines = [
        "┌────────────────────────────────────────────────────┐",
        "│                                                    │",
        "│           [bold bright_cyan]🏢 L O B B Y[/bold bright_cyan]                          │",
        "│                                                    │",
        "│        [bright_yellow]Intelligent AI Task Orchestration[/bright_yellow]         │",
        "│        [dim]Your concierge for any task[/dim]             │",
        "│                                                    │",
        "└────────────────────────────────────────────────────┘",
    ]

    for line in banner_lines:
        console.print(line, style="bright_white")

    console.print(
        "   [dim]Welcome to your AI concierge service[/dim]", justify="center"
    )
    console.print()


def print_section_header(title: str, icon: str = "▮▮▮"):
    """
    Print a styled section header.

    Args:
        title: Section title
        icon: Optional icon/decoration
    """
    console = get_console()
    console.print(f"\n[neon_cyan]{icon} {title.upper()} {icon}[/neon_cyan]")


def print_success(message: str):
    """Print a success message."""
    console = get_console()
    console.print(f"[success]✅ {message}[/success]")


def print_error(message: str):
    """Print an error message."""
    console = get_console()
    console.print(f"[danger]❌ {message}[/danger]")


def print_warning(message: str):
    """Print a warning message."""
    console = get_console()
    console.print(f"[warning]⚠️  {message}[/warning]")


def print_info(message: str):
    """Print an info message."""
    console = get_console()
    console.print(f"[primary]ℹ️  {message}[/primary]")


def print_subtle(message: str):
    """Print a subtle/muted message."""
    console = get_console()
    console.print(f"[dim]{message}[/dim]")
