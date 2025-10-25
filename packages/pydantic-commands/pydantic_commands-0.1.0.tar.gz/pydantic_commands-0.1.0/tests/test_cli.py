"""Tests for the host_cli function."""

from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel, Field

from pydantic_commands import BaseCommand, command_registry, host_cli


class CliTestCommand(BaseCommand):
    """Test command for host_cli tests."""

    name = "testcmd"
    help = "Test command"

    class Arguments(BaseModel):
        value: str = Field(..., description="Test value")

    def handle(self, args: Arguments) -> None:
        self.result = f"Executed with: {args.value}"
        print(f"Result: {args.value}")


@pytest.fixture
def clean_registry() -> Any:
    """Clean the command registry before each test."""
    original_items = dict(command_registry.registry)
    command_registry._registry.clear()

    yield command_registry

    # Restore
    command_registry._registry.clear()
    command_registry._registry.update(original_items)


def test_host_cli_basic_execution(
    clean_registry: pytest.fixture, capsys: pytest.fixture
) -> None:
    """Test that host_cli executes a command successfully."""
    cmd = CliTestCommand()
    clean_registry.register()(cmd)

    # Mock sys.exit to prevent actual exit
    with patch("sys.exit") as mock_exit:
        with patch("sys.argv", ["cli.py", "testcmd", "--value", "test123"]):
            host_cli()

    # Check that sys.exit was called with success code
    mock_exit.assert_called_once_with(0)

    # Check output
    captured = capsys.readouterr()
    assert "Result: test123" in captured.out


def test_host_cli_with_explicit_argv(clean_registry: pytest.fixture) -> None:
    """Test host_cli with explicit argv parameter."""
    cmd = CliTestCommand()
    clean_registry.register()(cmd)

    with patch("sys.exit") as mock_exit:
        host_cli(argv=["testcmd", "--value", "explicit"])

    mock_exit.assert_called_once_with(0)


def test_host_cli_with_prog_name(
    clean_registry: pytest.fixture, capsys: pytest.fixture
) -> None:
    """Test host_cli with custom program name."""
    cmd = CliTestCommand()
    clean_registry.register()(cmd)

    with patch("sys.exit"):
        host_cli(argv=["--help"], prog_name="myapp")

    # Check that help was shown (exit code 0 from --help)
    captured = capsys.readouterr()
    assert "myapp" in captured.out


def test_host_cli_unknown_command(clean_registry: pytest.fixture) -> None:
    """Test that unknown command exits with error code."""
    with patch("sys.exit") as mock_exit:
        host_cli(argv=["unknown", "--value", "test"])

    mock_exit.assert_called_once_with(1)


def test_host_cli_no_arguments(
    clean_registry: pytest.fixture, capsys: pytest.fixture
) -> None:
    """Test that no arguments shows help."""
    cmd = CliTestCommand()
    clean_registry.register()(cmd)

    with patch("sys.exit"):
        host_cli(argv=[])

    # Should show help and exit (argparse exits with 0 for --help)
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "Usage:" in captured.out


def test_host_cli_command_error(clean_registry: pytest.fixture) -> None:
    """Test that command errors result in non-zero exit code."""
    from pydantic_commands import CommandError

    class ErrorCommand(BaseCommand):
        name = "error"

        def handle(self, args: object) -> None:
            raise CommandError("Test error")

    clean_registry.register()(ErrorCommand())

    with patch("sys.exit") as mock_exit:
        host_cli(argv=["error"])

    # Should exit with error code
    mock_exit.assert_called_once_with(1)


def test_host_cli_integration_example(
    clean_registry: pytest.fixture, capsys: pytest.fixture
) -> None:
    """Test a realistic integration scenario."""

    class CreateCommand(BaseCommand):
        name = "create"

        class Arguments(BaseModel):
            name: str
            count: int = 1

        def handle(self, args: Arguments) -> None:
            for i in range(args.count):
                print(f"Creating {args.name} #{i + 1}")

    clean_registry.register()(CreateCommand())

    with patch("sys.exit") as mock_exit:
        host_cli(argv=["create", "--name", "item", "--count", "3"])

    mock_exit.assert_called_once_with(0)

    captured = capsys.readouterr()
    assert "Creating item #1" in captured.out
    assert "Creating item #2" in captured.out
    assert "Creating item #3" in captured.out
