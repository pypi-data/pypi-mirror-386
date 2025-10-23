"""
LOBBY UI components for interactive CLI.
"""

from .prompts import (
    autocomplete,
    confirm,
    format_choices_with_descriptions,
    has_interactive_backend,
    input_text,
    is_interactive,
    number_input,
    password,
    path_select,
    select_many,
    select_one,
    show_spinner,
)
from .theme import (
    COLORS,
    NYC_THEME,
    get_console,
    get_inquirer_style,
    get_questionary_style,
    print_banner,
    print_error,
    print_info,
    print_section_header,
    print_subtle,
    print_success,
    print_warning,
)

__all__ = [
    # Prompt functions
    "is_interactive",
    "has_interactive_backend",
    "input_text",
    "password",
    "confirm",
    "select_one",
    "select_many",
    "autocomplete",
    "path_select",
    "number_input",
    "show_spinner",
    "format_choices_with_descriptions",
    # Theme functions
    "get_console",
    "get_inquirer_style",
    "get_questionary_style",
    "print_banner",
    "print_section_header",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_subtle",
    "NYC_THEME",
    "COLORS",
]
