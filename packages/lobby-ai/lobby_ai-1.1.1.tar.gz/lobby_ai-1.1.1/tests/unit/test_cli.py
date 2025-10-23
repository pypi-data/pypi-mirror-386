"""Test the CLI functionality."""

from typer.testing import CliRunner

from doorman.cli.main import app

runner = CliRunner()


def test_app_help():
    """Test that the app shows help correctly."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Doorman" in result.stdout or "90's sprite-themed" in result.stdout


def test_plan_command():
    """Test the plan command."""
    result = runner.invoke(app, ["plan", "Create a simple Python script"])
    assert result.exit_code == 0
    assert "Planning task" in result.stdout


def test_tui_command():
    """Test the TUI command."""
    result = runner.invoke(app, ["tui"])
    assert result.exit_code == 0
    assert "TUI interface" in result.stdout


def test_mcp_server_command():
    """Test the MCP server command."""
    result = runner.invoke(app, ["mcp-server"])
    assert result.exit_code == 0
    assert "MCP server" in result.stdout


def test_mcp_client_command():
    """Test the MCP client command."""
    result = runner.invoke(app, ["mcp-client"])
    assert result.exit_code == 0
    assert "MCP Client" in result.stdout


def test_auth_command():
    """Test the auth command."""
    result = runner.invoke(app, ["auth"])
    assert result.exit_code == 0
    assert "Authentication" in result.stdout
