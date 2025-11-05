"""Tests for kagura.utils.json_helpers module."""

import json

import pytest

from kagura.utils.json_helpers import (
    decode_chromadb_metadata,
    encode_chromadb_metadata,
    safe_json_loads,
)


class TestEncodeChromadbMetadata:
    """Tests for encode_chromadb_metadata function."""

    def test_encode_list(self):
        """Test encoding a list to JSON string."""
        metadata = {"tags": ["python", "ai", "ml"]}
        result = encode_chromadb_metadata(metadata)
        assert result == {"tags": '["python", "ai", "ml"]'}
        # Verify it's a valid JSON string
        assert json.loads(result["tags"]) == ["python", "ai", "ml"]

    def test_encode_dict(self):
        """Test encoding a dict to JSON string."""
        metadata = {"config": {"model": "gpt-4", "temperature": 0.7}}
        result = encode_chromadb_metadata(metadata)
        assert "config" in result
        assert isinstance(result["config"], str)
        assert json.loads(result["config"]) == {"model": "gpt-4", "temperature": 0.7}

    def test_preserve_scalars(self):
        """Test that scalar values are preserved as-is."""
        metadata = {
            "count": 42,
            "active": True,
            "name": "test",
            "score": 3.14,
        }
        result = encode_chromadb_metadata(metadata)
        assert result == metadata  # Should be unchanged

    def test_mixed_types(self):
        """Test encoding metadata with mixed types."""
        metadata = {
            "tags": ["tag1", "tag2"],
            "count": 5,
            "config": {"key": "value"},
            "active": True,
            "description": "test metadata",
        }
        result = encode_chromadb_metadata(metadata)

        assert isinstance(result["tags"], str)
        assert result["count"] == 5
        assert isinstance(result["config"], str)
        assert result["active"] is True
        assert result["description"] == "test metadata"

        # Verify encoded values are valid JSON
        assert json.loads(result["tags"]) == ["tag1", "tag2"]
        assert json.loads(result["config"]) == {"key": "value"}

    def test_empty_metadata(self):
        """Test encoding empty metadata."""
        result = encode_chromadb_metadata({})
        assert result == {}

    def test_nested_structures(self):
        """Test encoding deeply nested structures."""
        metadata = {
            "nested": {
                "level1": {
                    "level2": ["a", "b", "c"]
                }
            }
        }
        result = encode_chromadb_metadata(metadata)
        assert isinstance(result["nested"], str)
        decoded = json.loads(result["nested"])
        assert decoded == metadata["nested"]

    def test_unicode_handling(self):
        """Test encoding with Unicode characters."""
        metadata = {"tags": ["日本語", "中文", "한국어"]}
        result = encode_chromadb_metadata(metadata)
        assert isinstance(result["tags"], str)
        decoded = json.loads(result["tags"])
        assert decoded == ["日本語", "中文", "한국어"]

    def test_empty_list_and_dict(self):
        """Test encoding empty list and dict."""
        metadata = {"empty_list": [], "empty_dict": {}}
        result = encode_chromadb_metadata(metadata)
        assert result["empty_list"] == "[]"
        assert result["empty_dict"] == "{}"


class TestDecodeChromadbMetadata:
    """Tests for decode_chromadb_metadata function."""

    def test_decode_list_string(self):
        """Test decoding JSON list string."""
        metadata = {"tags": '["python", "ai"]'}
        result = decode_chromadb_metadata(metadata)
        assert result == {"tags": ["python", "ai"]}

    def test_decode_dict_string(self):
        """Test decoding JSON dict string."""
        metadata = {"config": '{"model": "gpt-4"}'}
        result = decode_chromadb_metadata(metadata)
        assert result == {"config": {"model": "gpt-4"}}

    def test_preserve_scalars(self):
        """Test that scalar values are preserved."""
        metadata = {
            "count": 42,
            "active": True,
            "name": "test",
        }
        result = decode_chromadb_metadata(metadata)
        assert result == metadata

    def test_preserve_non_json_strings(self):
        """Test that non-JSON strings are preserved."""
        metadata = {
            "description": "This is a normal string",
            "path": "/home/user/file.txt",
        }
        result = decode_chromadb_metadata(metadata)
        assert result == metadata

    def test_handle_malformed_json(self):
        """Test that malformed JSON strings are preserved."""
        metadata = {
            "malformed_list": "[invalid",
            "malformed_dict": "{bad json}",
            "count": 5,
        }
        result = decode_chromadb_metadata(metadata)
        # Malformed JSON should be preserved as-is
        assert result["malformed_list"] == "[invalid"
        assert result["malformed_dict"] == "{bad json}"
        assert result["count"] == 5

    def test_mixed_types(self):
        """Test decoding metadata with mixed types."""
        metadata = {
            "tags": '["tag1", "tag2"]',
            "count": 5,
            "config": '{"key": "value"}',
            "active": True,
            "description": "normal string",
        }
        result = decode_chromadb_metadata(metadata)

        assert result["tags"] == ["tag1", "tag2"]
        assert result["count"] == 5
        assert result["config"] == {"key": "value"}
        assert result["active"] is True
        assert result["description"] == "normal string"

    def test_empty_metadata(self):
        """Test decoding empty metadata."""
        result = decode_chromadb_metadata({})
        assert result == {}

    def test_nested_json_structures(self):
        """Test decoding nested JSON structures."""
        metadata = {"nested": '{"level1": {"level2": ["a", "b"]}}'}
        result = decode_chromadb_metadata(metadata)
        assert result == {"nested": {"level1": {"level2": ["a", "b"]}}}

    def test_unicode_in_json_string(self):
        """Test decoding JSON with Unicode."""
        metadata = {"tags": '["日本語", "中文"]'}
        result = decode_chromadb_metadata(metadata)
        assert result == {"tags": ["日本語", "中文"]}

    def test_json_null(self):
        """Test that JSON null string is preserved (not parsed)."""
        # "null" doesn't start with [ or {, so it's preserved as string
        metadata = {"value": "null"}
        result = decode_chromadb_metadata(metadata)
        assert result == {"value": "null"}  # Preserved as string

    def test_json_primitives_in_string(self):
        """Test that JSON primitives in strings are preserved."""
        metadata = {
            "number": "123",  # Doesn't start with [ or {
            "bool": "true",   # Doesn't start with [ or {
        }
        result = decode_chromadb_metadata(metadata)
        # Should preserve as strings (not parsed to int/bool)
        assert result == metadata


class TestSafeJsonLoads:
    """Tests for safe_json_loads function."""

    def test_parse_valid_json_list(self):
        """Test parsing valid JSON list."""
        result = safe_json_loads('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_parse_valid_json_dict(self):
        """Test parsing valid JSON dict."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_valid_json_primitives(self):
        """Test parsing JSON primitives."""
        assert safe_json_loads('"string"') == "string"
        assert safe_json_loads('123') == 123
        assert safe_json_loads('true') is True
        assert safe_json_loads('false') is False
        assert safe_json_loads('3.14') == 3.14

    def test_invalid_json_returns_default(self):
        """Test that invalid JSON returns default value."""
        result = safe_json_loads('invalid json', default=[])
        assert result == []

    def test_non_string_input_returned_as_is(self):
        """Test that non-string inputs are returned as-is."""
        assert safe_json_loads([1, 2, 3]) == [1, 2, 3]
        assert safe_json_loads({"key": "value"}) == {"key": "value"}
        assert safe_json_loads(42) == 42
        assert safe_json_loads(True) is True

    def test_none_input_returns_default(self):
        """Test that None input returns default."""
        result = safe_json_loads(None, default="fallback")
        assert result == "fallback"

    def test_json_null_returns_default(self):
        """Test that JSON null returns default."""
        result = safe_json_loads("null", default="fallback")
        assert result == "fallback"

    def test_type_validation_success(self):
        """Test type validation when type matches."""
        result = safe_json_loads('["a", "b"]', expected_type=list)
        assert result == ["a", "b"]

    def test_type_validation_failure(self):
        """Test type validation when type doesn't match."""
        result = safe_json_loads('["a", "b"]', expected_type=dict, default={})
        assert result == {}

    def test_type_validation_with_dict(self):
        """Test type validation with dict."""
        result = safe_json_loads('{"key": "value"}', expected_type=dict)
        assert result == {"key": "value"}

        # Wrong type should return default
        result = safe_json_loads('{"key": "value"}', expected_type=list, default=[])
        assert result == []

    def test_empty_string_returns_default(self):
        """Test that empty string returns default."""
        result = safe_json_loads("", default="empty")
        assert result == "empty"

    def test_default_is_none_by_default(self):
        """Test that default parameter defaults to None."""
        result = safe_json_loads("invalid")
        assert result is None

    def test_unicode_json(self):
        """Test parsing JSON with Unicode."""
        result = safe_json_loads('["日本語", "中文"]')
        assert result == ["日本語", "中文"]

    def test_nested_structures(self):
        """Test parsing nested JSON structures."""
        json_str = '{"level1": {"level2": {"level3": ["a", "b"]}}}'
        result = safe_json_loads(json_str)
        assert result == {"level1": {"level2": {"level3": ["a", "b"]}}}


class TestRoundTrip:
    """Tests for encode/decode round-trip consistency."""

    def test_list_round_trip(self):
        """Test that encoding then decoding a list returns original."""
        original = {"tags": ["python", "ai"]}
        encoded = encode_chromadb_metadata(original)
        decoded = decode_chromadb_metadata(encoded)
        assert decoded == original

    def test_dict_round_trip(self):
        """Test that encoding then decoding a dict returns original."""
        original = {"config": {"model": "gpt-4", "temp": 0.7}}
        encoded = encode_chromadb_metadata(original)
        decoded = decode_chromadb_metadata(encoded)
        assert decoded == original

    def test_mixed_types_round_trip(self):
        """Test round-trip with mixed types."""
        original = {
            "tags": ["tag1", "tag2"],
            "count": 42,
            "config": {"key": "value"},
            "active": True,
            "description": "test",
        }
        encoded = encode_chromadb_metadata(original)
        decoded = decode_chromadb_metadata(encoded)
        assert decoded == original

    def test_nested_structures_round_trip(self):
        """Test round-trip with nested structures."""
        original = {
            "nested": {
                "level1": {
                    "level2": ["a", "b", "c"]
                }
            },
            "count": 3,
        }
        encoded = encode_chromadb_metadata(original)
        decoded = decode_chromadb_metadata(encoded)
        assert decoded == original

    def test_unicode_round_trip(self):
        """Test round-trip with Unicode characters."""
        original = {
            "tags": ["日本語", "中文", "한국어"],
            "description": "多言語テスト",
        }
        encoded = encode_chromadb_metadata(original)
        decoded = decode_chromadb_metadata(encoded)
        assert decoded == original
