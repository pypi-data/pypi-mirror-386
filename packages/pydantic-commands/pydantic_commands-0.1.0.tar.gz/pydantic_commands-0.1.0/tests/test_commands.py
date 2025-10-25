"""Tests for pydantic-commands."""

from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, Field

from pydantic_commands import BaseCommand, CommandError, CommandExecutor, command
from pydantic_commands.exceptions import CommandValidationError
from pydantic_commands.registry import command_registry


# Test Models
class UserArgs(BaseModel):
    """Test argument model for user creation."""

    username: str = Field(..., description="Username for the new user")
    email: str = Field(..., description="Email address")
    age: int = Field(default=18, description="User age")
    is_active: bool = Field(default=True, description="Whether user is active")


class FileArgs(BaseModel):
    """Test argument model with file paths."""

    input_file: Path = Field(..., description="Input file path")
    output_file: Path = Field(..., description="Output file path")
    overwrite: bool = Field(default=False, description="Overwrite existing files")


class Status(str, Enum):
    """Test enum for status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class StatusArgs(BaseModel):
    """Test argument model with enum."""

    status: Status = Field(..., description="User status")
    message: str = Field(default="", description="Optional message")


class ListArgs(BaseModel):
    """Test argument model with lists."""

    tags: list[str] = Field(default_factory=list, description="List of tags")
    ids: list[int] = Field(default_factory=list, description="List of IDs")


# Test Commands
class CreateUserCommand(BaseCommand):
    """Test command using class-based approach."""

    name = "createuser"
    help = "Create a new user"
    Arguments = UserArgs

    def handle(self, args: UserArgs) -> None:
        self.result = f"Created user: {args.username} ({args.email}), age: {args.age}"


class SimpleCommand(BaseCommand):
    """Command without Pydantic arguments."""

    name = "simple"
    help = "Simple command"

    def handle(self, args: object) -> None:
        self.result = "Simple command executed"


@command(name="testfunc", help="Test function command", arguments=UserArgs)
def test_function_command(args: UserArgs) -> None:
    """Test function-based command."""
    print(f"Function command: {args.username}")


# Fixtures
@pytest.fixture
def clean_registry() -> Any:
    """Clean the command registry before each test."""
    # Save current commands
    original_commands = dict(command_registry.registry)

    # Clear registry
    command_registry._registry.clear()

    yield command_registry

    # Restore original commands
    command_registry._registry.clear()
    command_registry._registry.update(original_commands)


@pytest.fixture
def user_command() -> CreateUserCommand:
    """Create a CreateUserCommand instance."""
    return CreateUserCommand()


@pytest.fixture
def simple_command() -> SimpleCommand:
    """Create a SimpleCommand instance."""
    return SimpleCommand()


# Tests for BaseCommand
def test_command_initialization(user_command: CreateUserCommand) -> None:
    """Test that command is properly initialized."""
    assert user_command.name == "createuser"
    assert user_command.help == "Create a new user"
    assert user_command.Arguments == UserArgs


def test_command_name_inference() -> None:
    """Test that command name is inferred from class name."""

    class MyTestCommand(BaseCommand):
        def handle(self, args: object) -> None:
            pass

    cmd = MyTestCommand()
    assert cmd.name == "mytest"


def test_parser_creation(user_command: CreateUserCommand) -> None:
    """Test that parser is created with correct arguments."""
    parser = user_command.create_parser()

    # Check that arguments are added
    namespace = parser.parse_args(["--username", "john", "--email", "john@example.com"])
    assert namespace.username == "john"
    assert namespace.email == "john@example.com"
    assert namespace.age == 18  # default value


def test_required_arguments(user_command: CreateUserCommand) -> None:
    """Test that required arguments are enforced."""
    parser = user_command.create_parser()

    with pytest.raises(SystemExit):
        # Missing required arguments should fail
        parser.parse_args([])


def test_argument_parsing_with_defaults(user_command: CreateUserCommand) -> None:
    """Test parsing arguments with default values."""
    args = user_command.parse_arguments(
        ["--username", "jane", "--email", "jane@example.com"]
    )

    assert args.username == "jane"
    assert args.email == "jane@example.com"
    assert args.age == 18
    assert args.is_active is True


def test_argument_parsing_with_overrides(user_command: CreateUserCommand) -> None:
    """Test parsing arguments with overridden defaults."""
    args = user_command.parse_arguments(
        [
            "--username",
            "bob",
            "--email",
            "bob@example.com",
            "--age",
            "25",
            "--no-is-active",  # Default is True, so use --no-is-active to set to False
        ]
    )

    assert args.username == "bob"
    assert args.age == 25
    assert args.is_active is False  # Flag should set it to False


def test_command_execution(user_command: CreateUserCommand) -> None:
    """Test command execution."""
    exit_code = user_command.execute(
        ["--username", "test", "--email", "test@example.com"]
    )

    assert exit_code == 0
    assert "Created user: test" in user_command.result


def test_command_error_handling() -> None:
    """Test that CommandError is handled properly."""

    class ErrorCommand(BaseCommand):
        name = "error"

        def handle(self, args: object) -> None:
            raise CommandError("Something went wrong")

    cmd = ErrorCommand()
    exit_code = cmd.execute([])

    assert exit_code == 1


# Tests for function-based commands
def test_function_command_decorator() -> None:
    """Test that @command decorator creates a command class."""

    @command(name="testdec", help="Test decorator", arguments=UserArgs)
    def my_command(args: UserArgs) -> None:
        pass

    assert issubclass(my_command, BaseCommand)


def test_function_command_execution() -> None:
    """Test executing a function-based command."""
    results = []

    @command(name="functest", arguments=UserArgs, register=False)
    def func_cmd(args: UserArgs) -> None:
        results.append(args.username)

    cmd_instance = func_cmd()
    cmd_instance.execute(["--username", "alice", "--email", "alice@example.com"])

    assert "alice" in results


# Tests for enum arguments
def test_enum_argument_parsing() -> None:
    """Test parsing enum arguments."""

    class StatusCommand(BaseCommand):
        name = "status"
        Arguments = StatusArgs

        def handle(self, args: StatusArgs) -> None:
            self.status = args.status

    cmd = StatusCommand()
    args = cmd.parse_arguments(["--status", "active"])

    assert args.status == Status.ACTIVE


def test_enum_argument_validation() -> None:
    """Test that invalid enum values are rejected."""

    class StatusCommand(BaseCommand):
        name = "status"
        Arguments = StatusArgs

        def handle(self, args: StatusArgs) -> None:
            pass

    cmd = StatusCommand()
    parser = cmd.create_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["--status", "invalid"])


# Tests for list arguments
def test_list_argument_parsing() -> None:
    """Test parsing list arguments."""

    class TagCommand(BaseCommand):
        name = "tag"
        Arguments = ListArgs

        def handle(self, args: ListArgs) -> None:
            self.tags = args.tags
            self.ids = args.ids

    cmd = TagCommand()
    args = cmd.parse_arguments(
        ["--tags", "python", "testing", "cli", "--ids", "1", "2", "3"]
    )

    assert args.tags == ["python", "testing", "cli"]
    assert args.ids == [1, 2, 3]


def test_empty_list_arguments() -> None:
    """Test that empty lists work as defaults."""

    class TagCommand(BaseCommand):
        name = "tag"
        Arguments = ListArgs

        def handle(self, args: ListArgs) -> None:
            self.tags = args.tags

    cmd = TagCommand()
    args = cmd.parse_arguments([])

    assert args.tags == []
    assert args.ids == []


# Tests for Path arguments
def test_path_argument_parsing() -> None:
    """Test parsing Path arguments."""

    class FileCommand(BaseCommand):
        name = "file"
        Arguments = FileArgs

        def handle(self, args: FileArgs) -> None:
            self.input_file = args.input_file

    cmd = FileCommand()
    args = cmd.parse_arguments(
        ["--input-file", "/tmp/input.txt", "--output-file", "/tmp/output.txt"]
    )

    assert isinstance(args.input_file, Path)
    assert str(args.input_file) == "/tmp/input.txt"


# Tests for CommandExecutor
def test_executor_list_commands(clean_registry: Any) -> None:
    """Test listing available commands."""
    cmd1 = CreateUserCommand()
    cmd2 = SimpleCommand()

    clean_registry.register()(cmd1)
    clean_registry.register()(cmd2)

    executor = CommandExecutor()
    commands = executor.list_commands()

    assert "createuser" in commands
    assert "simple" in commands


def test_executor_execute_command(clean_registry: Any) -> None:
    """Test executing a command through executor."""
    cmd = CreateUserCommand()
    clean_registry.register()(cmd)

    executor = CommandExecutor()
    exit_code = executor.execute(
        ["createuser", "--username", "exec_test", "--email", "exec@example.com"]
    )

    assert exit_code == 0


def test_executor_unknown_command(clean_registry: Any) -> None:
    """Test executing an unknown command."""
    executor = CommandExecutor()
    exit_code = executor.execute(["unknown", "--help"])

    assert exit_code == 1


def test_executor_no_command() -> None:
    """Test executor with no command specified."""
    executor = CommandExecutor()

    # Should raise SystemExit when showing help
    with pytest.raises(SystemExit) as exc_info:
        executor.execute([])

    # Help shows with exit code 0
    assert exc_info.value.code == 0


# Tests for command registry
def test_registry_registration(clean_registry: Any) -> None:
    """Test registering commands in registry."""
    cmd = CreateUserCommand()
    clean_registry.register()(cmd)

    assert "createuser" in clean_registry.registry.keys()
    assert clean_registry.get("createuser") == cmd


def test_registry_duplicate_registration(clean_registry: Any) -> None:
    """Test that duplicate command names are handled."""
    cmd1 = CreateUserCommand()
    cmd2 = CreateUserCommand()

    clean_registry.register()(cmd1)
    clean_registry.register()(cmd2)

    # Should have only one instance (last one wins)
    commands = list(clean_registry.registry.keys())
    assert commands.count("createuser") == 1


# Integration tests
def test_full_command_workflow(clean_registry: Any) -> None:
    """Test a complete command workflow from definition to execution."""

    class GreetCommand(BaseCommand):
        name = "greet"
        help = "Greet a user"

        class Arguments(BaseModel):
            name: str
            greeting: str = "Hello"

        def handle(self, args: Any) -> None:
            self.output = f"{args.greeting}, {args.name}!"

    cmd = GreetCommand()
    clean_registry.register()(cmd)

    executor = CommandExecutor()
    exit_code = executor.execute(["greet", "--name", "World", "--greeting", "Hi"])

    assert exit_code == 0
    assert cmd.output == "Hi, World!"


def test_command_with_validation_error() -> None:
    """Test that Pydantic validation errors are caught."""

    class AgeCommand(BaseCommand):
        name = "age"

        class Arguments(BaseModel):
            age: int = Field(..., ge=0, le=150)

        def handle(self, args: BaseModel) -> None:
            pass

    cmd = AgeCommand()

    # Invalid age should raise validation error
    with pytest.raises(CommandValidationError):  # Will be caught by execute()
        cmd.parse_arguments(["--age", "999"])
