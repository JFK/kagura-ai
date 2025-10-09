"""Tests for Command dataclass."""

import pytest

from kagura.commands.command import Command


def test_command_creation_basic():
    """Test basic command creation."""
    cmd = Command(
        name="test-cmd",
        description="Test command",
        template="# Test\nDo something",
    )

    assert cmd.name == "test-cmd"
    assert cmd.description == "Test command"
    assert cmd.template == "# Test\nDo something"
    assert cmd.model == "gpt-4o-mini"  # Default
    assert cmd.allowed_tools == []
    assert cmd.parameters == {}


def test_command_creation_full():
    """Test command creation with all fields."""
    cmd = Command(
        name="full-cmd",
        description="Full command",
        template="# Full\nExecute task",
        allowed_tools=["git", "gh"],
        model="gpt-4o",
        parameters={"file": "string", "count": "int"},
        metadata={"author": "test", "version": "1.0"},
    )

    assert cmd.name == "full-cmd"
    assert cmd.allowed_tools == ["git", "gh"]
    assert cmd.model == "gpt-4o"
    assert cmd.parameters == {"file": "string", "count": "int"}
    assert cmd.metadata == {"author": "test", "version": "1.0"}


def test_command_validation_empty_name():
    """Test that empty name raises ValueError."""
    with pytest.raises(ValueError, match="name cannot be empty"):
        Command(name="", description="Test", template="Content")


def test_command_validation_empty_template():
    """Test that empty template raises ValueError."""
    with pytest.raises(ValueError, match="template cannot be empty"):
        Command(name="test", description="Test", template="")


def test_command_validate_parameters_missing():
    """Test parameter validation with missing required parameter."""
    cmd = Command(
        name="test",
        description="Test",
        template="Content",
        parameters={"required_param": "string"},
    )

    with pytest.raises(ValueError, match="Required parameter missing: required_param"):
        cmd.validate_parameters({})


def test_command_validate_parameters_dict_required():
    """Test parameter validation with dict-style parameter definition."""
    cmd = Command(
        name="test",
        description="Test",
        template="Content",
        parameters={"file": {"type": "string", "required": True}},
    )

    # Missing required parameter
    with pytest.raises(ValueError, match="Required parameter missing: file"):
        cmd.validate_parameters({})

    # Valid
    cmd.validate_parameters({"file": "test.txt"})


def test_command_validate_parameters_dict_optional():
    """Test parameter validation with optional parameter."""
    cmd = Command(
        name="test",
        description="Test",
        template="Content",
        parameters={"file": {"type": "string", "required": False}},
    )

    # Optional parameter can be missing
    cmd.validate_parameters({})
    cmd.validate_parameters({"file": "test.txt"})


def test_command_validate_parameters_success():
    """Test successful parameter validation."""
    cmd = Command(
        name="test",
        description="Test",
        template="Content",
        parameters={"file": "string", "count": "int"},
    )

    # All parameters provided
    cmd.validate_parameters({"file": "test.txt", "count": 5})


def test_command_repr():
    """Test string representation."""
    cmd = Command(
        name="test-cmd",
        description="Test",
        template="Content",
        allowed_tools=["git"],
        parameters={"file": "string"},
    )

    repr_str = repr(cmd)
    assert "Command" in repr_str
    assert "test-cmd" in repr_str
    assert "tools=1" in repr_str
    assert "params=1" in repr_str


def test_command_repr_minimal():
    """Test string representation with minimal fields."""
    cmd = Command(name="minimal", description="Test", template="Content")

    repr_str = repr(cmd)
    assert "Command" in repr_str
    assert "minimal" in repr_str
    assert "tools" not in repr_str  # No tools
    assert "params" not in repr_str  # No params
