"""
Test suite for LOBBY interactive prompts functionality.
Tests both with and without interactive backends installed.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPromptEnvironment:
    """Test environment detection and backend availability."""

    def test_is_interactive_tty(self):
        """Test interactive detection when TTY is available."""
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            from lobby.ui.prompts import is_interactive

            assert is_interactive() == True

    def test_is_interactive_no_tty(self):
        """Test interactive detection when no TTY."""
        with patch("sys.stdin.isatty", return_value=False):
            from lobby.ui.prompts import is_interactive

            assert is_interactive() == False

    def test_is_interactive_ci_environment(self):
        """Test that CI environment forces non-interactive."""
        with (
            patch.dict(os.environ, {"CI": "1"}),
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            from lobby.ui.prompts import is_interactive

            assert is_interactive() == False

    def test_is_interactive_doorman_ci(self):
        """Test that DOORMAN_CI environment forces non-interactive."""
        with (
            patch.dict(os.environ, {"DOORMAN_CI": "1"}),
            patch("sys.stdin.isatty", return_value=True),
            patch("sys.stdout.isatty", return_value=True),
        ):
            from lobby.ui.prompts import is_interactive

            assert is_interactive() == False

    def test_has_interactive_backend(self):
        """Test backend detection."""
        from lobby.ui.prompts import (
            HAVE_INQUIRERPY,
            HAVE_QUESTIONARY,
            has_interactive_backend,
        )

        # Should match actual import status
        assert has_interactive_backend() == (HAVE_INQUIRERPY or HAVE_QUESTIONARY)


class TestPromptFallbacks:
    """Test fallback behavior when interactive backends are not available."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_input_text_fallback(self, mock_interactive):
        """Test input_text falls back to typer.prompt."""
        with patch("typer.prompt", return_value="test_value") as mock_prompt:
            from lobby.ui.prompts import input_text

            result = input_text("Test prompt", default="default")
            mock_prompt.assert_called_once_with("Test prompt", default="default")
            assert result == "test_value"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_password_fallback(self, mock_interactive):
        """Test password falls back to typer.prompt with hide_input."""
        with patch("typer.prompt", return_value="secret") as mock_prompt:
            from lobby.ui.prompts import password

            result = password("Enter password")
            mock_prompt.assert_called_once_with("Enter password", hide_input=True)
            assert result == "secret"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_confirm_fallback(self, mock_interactive):
        """Test confirm falls back to typer.confirm."""
        with patch("typer.confirm", return_value=True) as mock_confirm:
            from lobby.ui.prompts import confirm

            result = confirm("Are you sure?", default=False)
            mock_confirm.assert_called_once_with("Are you sure?", default=False)
            assert result == True

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_select_one_fallback(self, mock_interactive):
        """Test select_one fallback with numbered list."""
        with (
            patch("typer.prompt", return_value="2") as mock_prompt,
            patch("lobby.ui.prompts.get_console") as mock_console,
        ):
            from lobby.ui.prompts import select_one

            choices = ["option1", "option2", "option3"]
            result = select_one("Choose one", choices, default="option2")
            # Should show menu and accept number
            assert result == "option2"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_select_many_fallback(self, mock_interactive):
        """Test select_many fallback with comma-separated input."""
        with (
            patch("typer.prompt", return_value="opt1,opt3") as mock_prompt,
            patch("lobby.ui.prompts.get_console") as mock_console,
        ):
            from lobby.ui.prompts import select_many

            choices = ["opt1", "opt2", "opt3", "opt4"]
            result = select_many("Choose multiple", choices, default=["opt2"])
            # Should parse comma-separated
            assert result == ["opt1", "opt3"]


class TestWithInquirerPy:
    """Test with InquirerPy backend available (mocked)."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_input_text_with_inquirer(self, mock_interactive):
        """Test input_text uses InquirerPy when available."""
        mock_inquirer = MagicMock()
        mock_inquirer.text.return_value.execute.return_value = "inquirer_result"

        with patch("lobby.ui.prompts.inquirer", mock_inquirer):
            from lobby.ui.prompts import input_text

            result = input_text("Test prompt", default="default")
            mock_inquirer.text.assert_called_once()
            assert result == "inquirer_result"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_select_one_with_inquirer(self, mock_interactive):
        """Test select_one uses InquirerPy select."""
        mock_inquirer = MagicMock()
        mock_inquirer.select.return_value.execute.return_value = "selected"

        with patch("lobby.ui.prompts.inquirer", mock_inquirer):
            from lobby.ui.prompts import select_one

            result = select_one("Choose", ["a", "b", "c"], default="b")
            mock_inquirer.select.assert_called_once()
            assert result == "selected"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_select_many_with_inquirer(self, mock_interactive):
        """Test select_many uses InquirerPy checkbox."""
        mock_inquirer = MagicMock()
        mock_inquirer.checkbox.return_value.execute.return_value = ["a", "c"]

        with patch("lobby.ui.prompts.inquirer", mock_inquirer):
            from lobby.ui.prompts import select_many

            result = select_many("Choose multiple", ["a", "b", "c"], default=["b"])
            mock_inquirer.checkbox.assert_called_once()
            assert result == ["a", "c"]


class TestWithQuestionary:
    """Test with questionary backend available (mocked)."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_input_text_with_questionary(self, mock_interactive):
        """Test input_text uses questionary when InquirerPy not available."""
        mock_questionary = MagicMock()
        mock_questionary.text.return_value.ask.return_value = "questionary_result"

        with patch("lobby.ui.prompts.questionary", mock_questionary):
            from lobby.ui.prompts import input_text

            result = input_text("Test prompt", default="default")
            mock_questionary.text.assert_called_once()
            assert result == "questionary_result"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_password_with_questionary(self, mock_interactive):
        """Test password uses questionary.password."""
        mock_questionary = MagicMock()
        mock_questionary.password.return_value.ask.return_value = "secret123"

        with patch("lobby.ui.prompts.questionary", mock_questionary):
            from lobby.ui.prompts import password

            result = password("Enter password")
            mock_questionary.password.assert_called_once_with("Enter password")
            assert result == "secret123"


class TestNumberInput:
    """Test numeric input functionality."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_number_input_validation(self, mock_interactive):
        """Test number input with validation."""
        # Test valid number
        with (
            patch("typer.prompt", return_value="5.5") as mock_prompt,
            patch("lobby.ui.prompts.get_console") as mock_console,
        ):
            from lobby.ui.prompts import number_input

            result = number_input("Enter number", min_value=0, max_value=10)
            assert result == 5.5

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_number_input_integer_only(self, mock_interactive):
        """Test number input with integer-only mode."""
        with (
            patch("typer.prompt", return_value="5") as mock_prompt,
            patch("lobby.ui.prompts.get_console") as mock_console,
        ):
            from lobby.ui.prompts import number_input

            result = number_input("Enter integer", float_allowed=False)
            assert result == 5
            assert isinstance(result, int)


class TestPathSelect:
    """Test path selection functionality."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_path_select_with_inquirer(self, mock_interactive):
        """Test path selection with InquirerPy."""
        mock_inquirer = MagicMock()
        mock_inquirer.filepath.return_value.execute.return_value = "/test/path"

        with patch("lobby.ui.prompts.inquirer", mock_inquirer):
            from pathlib import Path

            from lobby.ui.prompts import path_select

            result = path_select("Choose file", exists=True)
            assert isinstance(result, Path)
            assert str(result) == "/test/path"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.is_interactive", return_value=False)
    def test_path_select_fallback_validation(self, mock_interactive):
        """Test path selection fallback with validation."""
        test_path = "/tmp/test_file.txt"

        # Create temporary file for testing
        with (
            patch("typer.prompt", return_value=test_path),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("lobby.ui.prompts.get_console"),
        ):
            from pathlib import Path

            from lobby.ui.prompts import path_select

            result = path_select("Choose file", only_files=True, exists=True)
            assert isinstance(result, Path)


class TestAutocomplete:
    """Test autocomplete functionality."""

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", True)
    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_autocomplete_with_fuzzy(self, mock_interactive):
        """Test autocomplete with fuzzy matching."""
        mock_inquirer = MagicMock()
        mock_inquirer.fuzzy.return_value.execute.return_value = "choice2"

        with (
            patch("lobby.ui.prompts.inquirer", mock_inquirer),
            patch("lobby.ui.prompts.EmptyInputValidator"),
            patch("lobby.ui.prompts.get_style"),
        ):
            from lobby.ui.prompts import autocomplete

            choices = ["choice1", "choice2", "choice3"]
            result = autocomplete("Select", choices, fuzzy=True)
            mock_inquirer.fuzzy.assert_called_once()
            assert result == "choice2"

    @patch("lobby.ui.prompts.HAVE_INQUIRERPY", False)
    @patch("lobby.ui.prompts.HAVE_QUESTIONARY", False)
    def test_autocomplete_fallback(self, *args):
        """Test autocomplete falls back to select_one."""
        with patch(
            "lobby.ui.prompts.select_one", return_value="selected"
        ) as mock_select:
            from lobby.ui.prompts import autocomplete

            result = autocomplete("Choose", ["a", "b", "c"])
            mock_select.assert_called_once()
            assert result == "selected"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_choices_with_descriptions(self):
        """Test formatting choices dictionary."""
        from lobby.ui.prompts import format_choices_with_descriptions

        choices_dict = {
            "opt1": "Description 1",
            "opt2": "Description 2",
            "opt3": "Description 3",
        }

        choices, descriptions = format_choices_with_descriptions(choices_dict)

        assert choices == ["opt1", "opt2", "opt3"]
        assert descriptions == choices_dict

    @patch("lobby.ui.prompts.is_interactive", return_value=True)
    def test_show_spinner(self, mock_interactive):
        """Test spinner functionality."""
        from lobby.ui.prompts import show_spinner

        def test_task():
            return "task_result"

        with patch("lobby.ui.prompts.get_console") as mock_console:
            result = show_spinner("Processing...", test_task)
            assert result == "task_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
