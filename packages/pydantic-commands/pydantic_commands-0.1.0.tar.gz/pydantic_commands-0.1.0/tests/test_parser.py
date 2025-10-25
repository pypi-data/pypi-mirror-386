"""Tests for the Pydantic argument parser."""

import argparse
from enum import Enum
from pathlib import Path
from typing import Union

import pytest
from pydantic import BaseModel, Field

from pydantic_commands.parser import PydanticArgumentParser


class SimpleModel(BaseModel):
    """Simple model for testing."""

    name: str
    age: int
    active: bool = True


class ComplexModel(BaseModel):
    """Complex model with various field types."""

    username: str = Field(..., description="The username")
    email: str = Field(..., description="Email address")
    age: int = Field(default=18, ge=0, le=150, description="User age")
    score: float = Field(default=0.0, description="Score")
    tags: list[str] = Field(default_factory=list, description="Tags")
    enabled: bool = Field(default=True, description="Enabled flag")


class PathModel(BaseModel):
    """Model with Path fields."""

    input_path: Path
    output_path: Path = Field(default=Path("/tmp/output"))


class Status(str, Enum):
    """Test enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class EnumModel(BaseModel):
    """Model with enum field."""

    status: Status
    message: str = ""


def test_simple_parser_creation() -> None:
    """Test creating a parser from a simple model."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(SimpleModel)
    pydantic_parser.add_arguments_to_parser(parser)

    # Parse arguments
    args = parser.parse_args(["--name", "John", "--age", "30"])

    assert args.name == "John"
    assert args.age == 30
    assert args.active is True  # default


def test_required_vs_optional() -> None:
    """Test that required and optional fields are handled correctly."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    # Should be able to parse with just required fields
    args = parser.parse_args(["--username", "test", "--email", "test@example.com"])

    assert args.username == "test"
    assert args.email == "test@example.com"
    assert args.age == 18  # default
    assert args.score == 0.0  # default


def test_string_field() -> None:
    """Test string field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(SimpleModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--name", "Alice", "--age", "25"])

    assert isinstance(args.name, str)
    assert args.name == "Alice"


def test_int_field() -> None:
    """Test integer field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(SimpleModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--name", "Bob", "--age", "42"])

    assert isinstance(args.age, int)
    assert args.age == 42


def test_float_field() -> None:
    """Test float field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(
        ["--username", "user", "--email", "user@example.com", "--score", "95.5"]
    )

    assert isinstance(args.score, float)
    assert args.score == 95.5


def test_bool_field_store_true() -> None:
    """Test boolean field with default False."""

    class BoolModel(BaseModel):
        verbose: bool = False

    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(BoolModel)
    pydantic_parser.add_arguments_to_parser(parser)

    # Without flag
    args = parser.parse_args([])
    assert args.verbose is False

    # With flag
    args = parser.parse_args(["--verbose"])
    assert args.verbose is True


def test_list_field() -> None:
    """Test list field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(
        [
            "--username",
            "user",
            "--email",
            "user@example.com",
            "--tags",
            "python",
            "cli",
            "testing",
        ]
    )

    assert isinstance(args.tags, list)
    assert args.tags == ["python", "cli", "testing"]


def test_empty_list() -> None:
    """Test that empty list defaults work."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--username", "user", "--email", "user@example.com"])

    assert args.tags == []


def test_path_field() -> None:
    """Test Path field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(PathModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(
        [
            "--input-path",
            "/home/user/input.txt",
            "--output-path",
            "/home/user/output.txt",
        ]
    )

    assert isinstance(args.input_path, Path)
    assert isinstance(args.output_path, Path)
    assert str(args.input_path) == "/home/user/input.txt"


def test_enum_field() -> None:
    """Test enum field parsing."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(EnumModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--status", "active"])

    assert args.status == "active"


def test_enum_choices() -> None:
    """Test that enum choices are enforced."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(EnumModel)
    pydantic_parser.add_arguments_to_parser(parser)

    with pytest.raises(SystemExit):
        parser.parse_args(["--status", "invalid"])


def test_field_description() -> None:
    """Test that field descriptions are used in help text."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    # Get help text
    help_text = parser.format_help()

    assert "The username" in help_text
    assert "Email address" in help_text
    assert "User age" in help_text


def test_underscore_to_dash_conversion() -> None:
    """Test that underscores in field names are converted to dashes."""

    class UnderscoreModel(BaseModel):
        first_name: str
        last_name: str

    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(UnderscoreModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--first-name", "John", "--last-name", "Doe"])

    assert args.first_name == "John"
    assert args.last_name == "Doe"


def test_optional_field() -> None:
    """Test optional field handling."""

    class OptionalModel(BaseModel):
        required: str
        optional: Union[str, None] = None

    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(OptionalModel)
    pydantic_parser.add_arguments_to_parser(parser)

    # Should work without optional field
    args = parser.parse_args(["--required", "value"])
    assert args.required == "value"
    assert args.optional is None


def test_str_to_bool_converter() -> None:
    """Test the string to boolean converter."""
    parser_helper = PydanticArgumentParser(SimpleModel)

    assert parser_helper._str_to_bool("true") is True
    assert parser_helper._str_to_bool("True") is True
    assert parser_helper._str_to_bool("yes") is True
    assert parser_helper._str_to_bool("1") is True

    assert parser_helper._str_to_bool("false") is False
    assert parser_helper._str_to_bool("False") is False
    assert parser_helper._str_to_bool("no") is False
    assert parser_helper._str_to_bool("0") is False

    with pytest.raises(argparse.ArgumentTypeError):
        parser_helper._str_to_bool("invalid")


def test_list_of_ints() -> None:
    """Test list of integers."""

    class ListIntModel(BaseModel):
        numbers: list[int] = Field(default_factory=list)

    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ListIntModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--numbers", "1", "2", "3", "4", "5"])

    assert args.numbers == [1, 2, 3, 4, 5]
    assert all(isinstance(n, int) for n in args.numbers)


def test_default_values() -> None:
    """Test that default values are properly set."""
    parser = argparse.ArgumentParser()
    pydantic_parser = PydanticArgumentParser(ComplexModel)
    pydantic_parser.add_arguments_to_parser(parser)

    args = parser.parse_args(["--username", "test", "--email", "test@example.com"])

    assert args.age == 18
    assert args.score == 0.0
    assert args.tags == []
    assert args.enabled is True
