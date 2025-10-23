"""
Interactive prompts abstraction layer for LOBBY CLI.
Provides Inquirer-style prompts with graceful fallback to Typer.
"""

import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Try to import interactive prompt libraries
HAVE_INQUIRERPY = False
HAVE_QUESTIONARY = False

try:
    from InquirerPy import inquirer
    from InquirerPy.base import Choice

    HAVE_INQUIRERPY = True
except ImportError:
    try:
        import questionary

        HAVE_QUESTIONARY = True
    except ImportError:
        pass


def is_interactive() -> bool:
    """Check if we're in an interactive environment."""
    # Check for CI environment variables
    if os.getenv("CI") or os.getenv("DOORMAN_CI"):
        return False

    # Check for explicit non-interactive flag
    if os.getenv("DOORMAN_INTERACTIVE") == "false":
        return False

    # Check if stdin/stdout are TTY
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def has_interactive_backend() -> bool:
    """Check if an interactive prompt backend is available."""
    return HAVE_INQUIRERPY or HAVE_QUESTIONARY


def input_text(
    message: str,
    default: Optional[str] = None,
    validate: Optional[Callable[[str], bool]] = None,
    multiline: bool = False,
) -> str:
    """
    Prompt for text input.

    Args:
        message: The prompt message
        default: Default value
        validate: Optional validation function
        multiline: Allow multiline input

    Returns:
        User input string
    """
    if HAVE_INQUIRERPY and is_interactive():
        kwargs = {"message": message}
        if default:
            kwargs["default"] = default
        if validate:
            kwargs["validate"] = validate
        if multiline:
            kwargs["multiline"] = True

        return inquirer.text(**kwargs).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        kwargs = {"message": message}
        if default:
            kwargs["default"] = default
        if validate:
            kwargs["validate"] = validate
        if multiline:
            kwargs["multiline"] = True

        result = questionary.text(**kwargs).ask()
        if result is None:  # User cancelled
            raise KeyboardInterrupt()
        return result

    # Fallback to basic input
    import typer

    return typer.prompt(message, default=default or "")


def password(message: str, validate: Optional[Callable[[str], bool]] = None) -> str:
    """
    Prompt for password/secret input.

    Args:
        message: The prompt message
        validate: Optional validation function

    Returns:
        User input string (hidden)
    """
    if HAVE_INQUIRERPY and is_interactive():
        kwargs = {"message": message}
        if validate:
            kwargs["validate"] = validate

        return inquirer.secret(**kwargs).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        result = questionary.password(message).ask()
        if result is None:
            raise KeyboardInterrupt()
        if validate and not validate(result):
            raise ValueError("Validation failed")
        return result

    # Fallback to Typer
    import typer

    result = typer.prompt(message, hide_input=True)
    if validate and not validate(result):
        raise ValueError("Validation failed")
    return result


def confirm(message: str, default: bool = True) -> bool:
    """
    Prompt for yes/no confirmation.

    Args:
        message: The prompt message
        default: Default value

    Returns:
        True if confirmed, False otherwise
    """
    if HAVE_INQUIRERPY and is_interactive():
        return inquirer.confirm(message=message, default=default).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        result = questionary.confirm(message, default=default).ask()
        if result is None:
            raise KeyboardInterrupt()
        return result

    # Fallback to Typer
    import typer

    return typer.confirm(message, default=default)


def select_one(
    message: str,
    choices: Sequence[str],
    default: Optional[str] = None,
    descriptions: Optional[Dict[str, str]] = None,
) -> str:
    """
    Prompt to select one option from a list.

    Args:
        message: The prompt message
        choices: List of choices
        default: Default selection
        descriptions: Optional descriptions for choices

    Returns:
        Selected choice
    """
    if not choices:
        raise ValueError("No choices provided")

    if HAVE_INQUIRERPY and is_interactive():
        if descriptions:
            prompt_choices = [
                Choice(value=choice, name=f"{choice} - {descriptions.get(choice, '')}")
                for choice in choices
            ]
        else:
            prompt_choices = list(choices)

        return inquirer.select(
            message=message, choices=prompt_choices, default=default
        ).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        if descriptions:
            prompt_choices = [
                questionary.Choice(
                    title=f"{choice} - {descriptions.get(choice, '')}", value=choice
                )
                for choice in choices
            ]
        else:
            prompt_choices = list(choices)

        result = questionary.select(
            message, choices=prompt_choices, default=default
        ).ask()

        if result is None:
            raise KeyboardInterrupt()
        return result

    # Fallback: show numbered list and prompt
    import typer
    from rich.console import Console

    console = Console()

    console.print(f"\n[bold]{message}[/bold]")
    for i, choice in enumerate(choices, 1):
        desc = (
            f" - {descriptions[choice]}"
            if descriptions and choice in descriptions
            else ""
        )
        marker = " (default)" if choice == default else ""
        console.print(f"  {i}. {choice}{desc}{marker}")

    while True:
        response = typer.prompt(
            "Enter your choice (number or text)", default=default or str(1)
        )

        # Try to parse as number
        try:
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            # Try to match as text
            if response in choices:
                return response
            # Try partial match
            matches = [c for c in choices if c.lower().startswith(response.lower())]
            if len(matches) == 1:
                return matches[0]

        console.print("[red]Invalid choice. Please try again.[/red]")


def select_many(
    message: str,
    choices: Sequence[str],
    default: Optional[Sequence[str]] = None,
    descriptions: Optional[Dict[str, str]] = None,
    min_selection: int = 0,
    max_selection: Optional[int] = None,
) -> List[str]:
    """
    Prompt to select multiple options from a list.

    Args:
        message: The prompt message
        choices: List of choices
        default: Default selections
        descriptions: Optional descriptions for choices
        min_selection: Minimum number of selections
        max_selection: Maximum number of selections

    Returns:
        List of selected choices
    """
    if not choices:
        return []

    default = list(default or [])

    if HAVE_INQUIRERPY and is_interactive():
        if descriptions:
            prompt_choices = [
                Choice(
                    value=choice,
                    name=f"{choice} - {descriptions.get(choice, '')}",
                    enabled=choice in default,
                )
                for choice in choices
            ]
        else:
            prompt_choices = [
                Choice(value=choice, enabled=choice in default) for choice in choices
            ]

        kwargs = {
            "message": message,
            "choices": prompt_choices,
        }

        if min_selection > 0:
            kwargs["validate"] = (
                lambda x: len(x) >= min_selection
                or f"Select at least {min_selection} options"
            )
        if max_selection:
            kwargs["validate"] = (
                lambda x: len(x) <= max_selection
                or f"Select at most {max_selection} options"
            )

        return inquirer.checkbox(**kwargs).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        if descriptions:
            prompt_choices = [
                questionary.Choice(
                    title=f"{choice} - {descriptions.get(choice, '')}",
                    value=choice,
                    checked=choice in default,
                )
                for choice in choices
            ]
        else:
            prompt_choices = [
                questionary.Choice(
                    title=choice, value=choice, checked=choice in default
                )
                for choice in choices
            ]

        result = questionary.checkbox(message, choices=prompt_choices).ask()

        if result is None:
            raise KeyboardInterrupt()

        if min_selection > 0 and len(result) < min_selection:
            raise ValueError(f"Select at least {min_selection} options")
        if max_selection and len(result) > max_selection:
            raise ValueError(f"Select at most {max_selection} options")

        return result or []

    # Fallback: comma-separated input
    import typer
    from rich.console import Console

    console = Console()

    console.print(f"\n[bold]{message}[/bold]")
    console.print("Available choices:")
    for choice in choices:
        desc = (
            f" - {descriptions[choice]}"
            if descriptions and choice in descriptions
            else ""
        )
        marker = " [dim](selected by default)[/dim]" if choice in default else ""
        console.print(f"  • {choice}{desc}{marker}")

    console.print("\n[dim]Enter choices separated by commas[/dim]")

    while True:
        response = typer.prompt(
            "Your selections", default=",".join(default) if default else ""
        )

        selected = [s.strip() for s in response.split(",") if s.strip()]

        # Validate selections
        invalid = [s for s in selected if s not in choices]
        if invalid:
            console.print(f"[red]Invalid choices: {', '.join(invalid)}[/red]")
            continue

        if min_selection > 0 and len(selected) < min_selection:
            console.print(f"[red]Select at least {min_selection} options[/red]")
            continue

        if max_selection and len(selected) > max_selection:
            console.print(f"[red]Select at most {max_selection} options[/red]")
            continue

        return selected


def autocomplete(
    message: str,
    choices: Sequence[str],
    default: Optional[str] = None,
    fuzzy: bool = True,
) -> str:
    """
    Prompt with autocomplete functionality.

    Args:
        message: The prompt message
        choices: List of choices for autocomplete
        default: Default value
        fuzzy: Enable fuzzy matching

    Returns:
        Selected or entered value
    """
    if HAVE_INQUIRERPY and is_interactive():
        from InquirerPy.validator import EmptyInputValidator

        return inquirer.fuzzy(
            message=message,
            choices=list(choices),
            default=default,
            validate=EmptyInputValidator(),
            match_exact=not fuzzy,
        ).execute()

    elif HAVE_QUESTIONARY and is_interactive():
        result = questionary.autocomplete(
            message, choices=list(choices), default=default or ""
        ).ask()

        if result is None:
            raise KeyboardInterrupt()
        return result

    # Fallback to select_one
    return select_one(message, choices, default)


def path_select(
    message: str,
    default: Optional[str] = None,
    only_directories: bool = False,
    only_files: bool = False,
    exists: bool = False,
) -> Path:
    """
    Prompt for file/directory path with autocomplete.

    Args:
        message: The prompt message
        default: Default path
        only_directories: Only allow directory selection
        only_files: Only allow file selection
        exists: Path must exist

    Returns:
        Selected path
    """
    if HAVE_INQUIRERPY and is_interactive():
        kwargs = {
            "message": message,
            "default": str(default) if default else "",
            "only_directories": only_directories,
            "only_files": only_files,
        }

        if exists:
            kwargs["validate"] = lambda x: Path(x).exists() or "Path does not exist"

        result = inquirer.filepath(**kwargs).execute()
        return Path(result)

    # Fallback to text input with validation
    import typer
    from rich.console import Console

    console = Console()

    while True:
        path_str = typer.prompt(message, default=str(default) if default else "")
        path = Path(path_str).expanduser().resolve()

        if exists and not path.exists():
            console.print(f"[red]Path does not exist: {path}[/red]")
            continue

        if only_directories and path.exists() and not path.is_dir():
            console.print(f"[red]Path is not a directory: {path}[/red]")
            continue

        if only_files and path.exists() and not path.is_file():
            console.print(f"[red]Path is not a file: {path}[/red]")
            continue

        return path


def number_input(
    message: str,
    default: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    float_allowed: bool = True,
) -> float:
    """
    Prompt for numeric input.

    Args:
        message: The prompt message
        default: Default value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        float_allowed: Allow decimal numbers

    Returns:
        Numeric value
    """
    if HAVE_INQUIRERPY and is_interactive():

        def validate(value):
            try:
                num = float(value) if float_allowed else int(value)
                if min_value is not None and num < min_value:
                    return f"Value must be at least {min_value}"
                if max_value is not None and num > max_value:
                    return f"Value must be at most {max_value}"
                return True
            except ValueError:
                return f"Invalid {'number' if float_allowed else 'integer'}"

        result = inquirer.text(
            message=message,
            default=str(default) if default is not None else "",
            validate=validate,
        ).execute()

        return float(result) if float_allowed else int(result)

    # Fallback to basic input with validation
    import typer
    from rich.console import Console

    console = Console()

    while True:
        value_str = typer.prompt(
            message, default=str(default) if default is not None else ""
        )

        try:
            value = float(value_str) if float_allowed else int(value_str)

            if min_value is not None and value < min_value:
                console.print(f"[red]Value must be at least {min_value}[/red]")
                continue

            if max_value is not None and value > max_value:
                console.print(f"[red]Value must be at most {max_value}[/red]")
                continue

            return value
        except ValueError:
            console.print(
                f"[red]Invalid {'number' if float_allowed else 'integer'}[/red]"
            )


# Utility functions for common patterns


def show_spinner(message: str, task: Callable) -> Any:
    """Show a spinner while executing a task."""
    if HAVE_INQUIRERPY and is_interactive():
        # InquirerPy doesn't have built-in spinner, use Rich
        from rich.console import Console

        console = Console()

        with console.status(message, spinner="dots"):
            return task()
    else:
        # Just print message and run task
        from rich.console import Console

        console = Console()
        console.print(f"[dim]{message}...[/dim]")
        return task()


def format_choices_with_descriptions(
    choices: Dict[str, str],
) -> tuple[List[str], Dict[str, str]]:
    """
    Format choices dictionary for use with select functions.

    Args:
        choices: Dict mapping choice values to descriptions

    Returns:
        Tuple of (choice_list, descriptions_dict)
    """
    return list(choices.keys()), choices
