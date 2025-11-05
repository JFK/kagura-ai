"""Tests for MCP common helpers (Phase 2)."""

import json

import pytest

from kagura.mcp.builtin.common import (
    format_error,
    format_success,
    handle_import_error,
    parse_json_dict,
    parse_json_list,
    require_api_key,
    to_bool,
    to_float_clamped,
    to_int,
)


class TestParseJsonList:
    """Tests for parse_json_list function."""

    def test_parse_string_json(self):
        """Test parsing JSON string."""
        result = parse_json_list('["tag1", "tag2"]')
        assert result == ["tag1", "tag2"]

    def test_parse_already_list(self):
        """Test that already-parsed list is returned as-is."""
        result = parse_json_list(["already", "parsed"])
        assert result == ["already", "parsed"]

    def test_parse_none_returns_default(self):
        """Test that None returns default."""
        result = parse_json_list(None)
        assert result == []

        result = parse_json_list(None, default=["custom"])
        assert result == ["custom"]

    def test_parse_invalid_json(self):
        """Test that invalid JSON returns default."""
        result = parse_json_list("invalid json", default=["fallback"])
        assert result == ["fallback"]

    def test_parse_wrong_type_returns_default(self):
        """Test that non-list JSON returns default."""
        result = parse_json_list('{"not": "a list"}', default=["fallback"])
        assert result == ["fallback"]

    def test_parse_non_string_non_list(self):
        """Test that unexpected types return default."""
        result = parse_json_list(42, default=["fallback"])
        assert result == ["fallback"]


class TestParseJsonDict:
    """Tests for parse_json_dict function."""

    def test_parse_string_json(self):
        """Test parsing JSON string."""
        result = parse_json_dict('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_already_dict(self):
        """Test that already-parsed dict is returned as-is."""
        result = parse_json_dict({"already": "parsed"})
        assert result == {"already": "parsed"}

    def test_parse_none_returns_default(self):
        """Test that None returns default."""
        result = parse_json_dict(None)
        assert result == {}

        result = parse_json_dict(None, default={"custom": "value"})
        assert result == {"custom": "value"}

    def test_parse_invalid_json(self):
        """Test that invalid JSON returns default."""
        result = parse_json_dict("invalid", default={"fallback": True})
        assert result == {"fallback": True}

    def test_parse_wrong_type_returns_default(self):
        """Test that non-dict JSON returns default."""
        result = parse_json_dict('["not", "a", "dict"]', default={"fallback": True})
        assert result == {"fallback": True}


class TestToInt:
    """Tests for to_int function."""

    def test_convert_string_to_int(self):
        """Test converting string to int."""
        assert to_int("42") == 42

    def test_convert_int_to_int(self):
        """Test that int is returned as-is."""
        assert to_int(42) == 42

    def test_convert_none_returns_default(self):
        """Test that None returns default."""
        assert to_int(None) == 0
        assert to_int(None, default=10) == 10

    def test_convert_invalid_returns_default(self):
        """Test that invalid string returns default."""
        assert to_int("invalid", default=99) == 99

    def test_clamp_to_min(self):
        """Test clamping to minimum value."""
        assert to_int("-10", min_val=0) == 0
        assert to_int("5", min_val=10) == 10

    def test_clamp_to_max(self):
        """Test clamping to maximum value."""
        assert to_int("100", max_val=50) == 50
        assert to_int("200", max_val=100) == 100

    def test_clamp_to_range(self):
        """Test clamping to min-max range."""
        assert to_int("5", min_val=10, max_val=20) == 10
        assert to_int("25", min_val=10, max_val=20) == 20
        assert to_int("15", min_val=10, max_val=20) == 15


class TestToFloatClamped:
    """Tests for to_float_clamped function."""

    def test_convert_string_to_float(self):
        """Test converting string to float."""
        assert to_float_clamped("0.8") == 0.8

    def test_convert_float_to_float(self):
        """Test that float is returned (clamped)."""
        assert to_float_clamped(0.8) == 0.8

    def test_convert_none_returns_default(self):
        """Test that None returns default."""
        assert to_float_clamped(None) == 0.5
        assert to_float_clamped(None, default=0.7) == 0.7

    def test_convert_invalid_returns_default(self):
        """Test that invalid string returns default."""
        assert to_float_clamped("invalid", default=0.6) == 0.6

    def test_clamp_high(self):
        """Test clamping high values."""
        assert to_float_clamped("1.5") == 1.0
        assert to_float_clamped("2.0", max_val=1.5) == 1.5

    def test_clamp_low(self):
        """Test clamping low values."""
        assert to_float_clamped("-0.5") == 0.0
        assert to_float_clamped("0.1", min_val=0.5) == 0.5

    def test_custom_range(self):
        """Test custom min-max range."""
        assert to_float_clamped("50", min_val=0, max_val=100) == 50.0
        assert to_float_clamped("150", min_val=0, max_val=100) == 100.0


class TestToBool:
    """Tests for to_bool function."""

    def test_convert_true_strings(self):
        """Test converting truthy strings."""
        assert to_bool("true") is True
        assert to_bool("True") is True
        assert to_bool("TRUE") is True
        assert to_bool("1") is True
        assert to_bool("yes") is True
        assert to_bool("on") is True

    def test_convert_false_strings(self):
        """Test converting falsy strings."""
        assert to_bool("false") is False
        assert to_bool("False") is False
        assert to_bool("FALSE") is False
        assert to_bool("0") is False
        assert to_bool("no") is False
        assert to_bool("off") is False

    def test_convert_bool_to_bool(self):
        """Test that bool is returned as-is."""
        assert to_bool(True) is True
        assert to_bool(False) is False

    def test_convert_none_returns_default(self):
        """Test that None returns default."""
        assert to_bool(None) is False
        assert to_bool(None, default=True) is True

    def test_convert_invalid_returns_default(self):
        """Test that invalid string returns default."""
        assert to_bool("invalid") is False
        assert to_bool("invalid", default=True) is True


class TestFormatSuccess:
    """Tests for format_success function."""

    def test_format_with_dict_data(self):
        """Test formatting success with dict data."""
        result = format_success({"key": "value"}, "Success")
        result_dict = json.loads(result)

        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Success"
        assert result_dict["key"] == "value"

    def test_format_with_string_data(self):
        """Test formatting success with string data."""
        result = format_success("result string", "Done")
        result_dict = json.loads(result)

        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Done"
        assert result_dict["result"] == "result string"

    def test_format_message_only(self):
        """Test formatting with message only."""
        result = format_success(message="Completed")
        result_dict = json.loads(result)

        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Completed"
        assert "data" not in result_dict

    def test_format_minimal(self):
        """Test minimal success response."""
        result = format_success()
        result_dict = json.loads(result)

        assert result_dict["status"] == "success"
        assert "message" not in result_dict


class TestFormatError:
    """Tests for format_error function."""

    def test_format_basic_error(self):
        """Test formatting basic error."""
        result = format_error("Something went wrong")
        result_dict = json.loads(result)

        assert result_dict["status"] == "error"
        assert result_dict["error"] == "Something went wrong"

    def test_format_with_details(self):
        """Test formatting error with details."""
        result = format_error("Not found", {"key": "missing"})
        result_dict = json.loads(result)

        assert result_dict["status"] == "error"
        assert result_dict["error"] == "Not found"
        assert result_dict["details"] == {"key": "missing"}

    def test_format_with_help(self):
        """Test formatting error with help text."""
        result = format_error("Invalid key", help_text="Use valid API key")
        result_dict = json.loads(result)

        assert result_dict["status"] == "error"
        assert result_dict["error"] == "Invalid key"
        assert result_dict["help"] == "Use valid API key"

    def test_format_with_all_fields(self):
        """Test formatting error with all fields."""
        result = format_error(
            "Failed", {"code": 500}, "Check logs"
        )
        result_dict = json.loads(result)

        assert result_dict["status"] == "error"
        assert result_dict["error"] == "Failed"
        assert result_dict["details"] == {"code": 500}
        assert result_dict["help"] == "Check logs"


class TestRequireApiKey:
    """Tests for require_api_key function."""

    def test_valid_api_key_returns_none(self):
        """Test that valid API key returns None."""
        result = require_api_key("valid-key", "Service")
        assert result is None

    def test_missing_api_key_returns_error(self):
        """Test that missing API key returns error."""
        result = require_api_key(None, "Brave Search", "BRAVE_API_KEY")
        assert result is not None

        result_dict = json.loads(result)
        assert result_dict["status"] == "error"
        assert "Brave Search API key required" in result_dict["error"]
        assert "BRAVE_API_KEY" in result_dict["help"]

    def test_empty_api_key_returns_error(self):
        """Test that empty API key returns error."""
        result = require_api_key("", "Service")
        assert result is not None

        result_dict = json.loads(result)
        assert result_dict["status"] == "error"


class TestHandleImportError:
    """Tests for handle_import_error function."""

    def test_format_import_error(self):
        """Test formatting import error message."""
        result = handle_import_error("chromadb", "pip install chromadb")
        result_dict = json.loads(result)

        assert result_dict["status"] == "error"
        assert "chromadb" in result_dict["error"]
        assert result_dict["details"]["package"] == "chromadb"
        assert "pip install chromadb" in result_dict["help"]
