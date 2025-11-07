"""Tests for kagura.utils.metadata module."""

from datetime import datetime

import pytest

from kagura.utils.metadata import (
    MemoryMetadata,
    build_full_metadata,
    extract_memory_fields,
    merge_metadata,
    prepare_for_chromadb,
    validate_importance,
)


class TestExtractMemoryFields:
    """Tests for extract_memory_fields function."""

    def test_extract_all_fields(self):
        """Test extracting all standard fields."""
        metadata = {
            "tags": ["python", "ai"],
            "importance": 0.8,
            "created_at": "2025-01-01T12:00:00",
            "updated_at": "2025-01-02T12:00:00",
            "custom_field": "value",
        }
        result = extract_memory_fields(metadata)

        assert result["tags"] == ["python", "ai"]
        assert result["importance"] == 0.8
        assert result["created_at"] == "2025-01-01T12:00:00"
        assert result["updated_at"] == "2025-01-02T12:00:00"
        assert result["user_metadata"] == {"custom_field": "value"}

    def test_extract_with_defaults(self):
        """Test extraction with missing fields uses defaults."""
        result = extract_memory_fields({})

        assert result["tags"] == []
        assert result["importance"] == 0.5
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["user_metadata"] == {}

    def test_extract_with_partial_fields(self):
        """Test extraction with only some fields present."""
        metadata = {
            "tags": ["test"],
            "custom": "data",
        }
        result = extract_memory_fields(metadata)

        assert result["tags"] == ["test"]
        assert result["importance"] == 0.5  # Default
        assert result["created_at"] is None
        assert result["updated_at"] is None
        assert result["user_metadata"] == {"custom": "data"}

    def test_extract_invalid_tags_type(self):
        """Test that invalid tags type defaults to empty list."""
        metadata = {"tags": "not_a_list"}
        result = extract_memory_fields(metadata)

        assert result["tags"] == []

    def test_extract_invalid_importance_type(self):
        """Test that invalid importance type defaults to 0.5."""
        metadata = {"importance": "invalid"}
        result = extract_memory_fields(metadata)

        assert result["importance"] == 0.5

    def test_extract_importance_clamping_high(self):
        """Test that importance >1.0 is clamped to 1.0."""
        metadata = {"importance": 1.5}
        result = extract_memory_fields(metadata)

        assert result["importance"] == 1.0

    def test_extract_importance_clamping_low(self):
        """Test that importance <0.0 is clamped to 0.0."""
        metadata = {"importance": -0.5}
        result = extract_memory_fields(metadata)

        assert result["importance"] == 0.0

    def test_extract_invalid_timestamp_type(self):
        """Test that invalid timestamp types become None."""
        metadata = {
            "created_at": 123,  # Not a string
            "updated_at": ["invalid"],
        }
        result = extract_memory_fields(metadata)

        assert result["created_at"] is None
        assert result["updated_at"] is None

    def test_extract_preserves_user_metadata(self):
        """Test that user metadata is preserved correctly."""
        metadata = {
            "tags": ["test"],
            "importance": 0.7,
            "custom1": "value1",
            "custom2": {"nested": "data"},
            "custom3": [1, 2, 3],
        }
        result = extract_memory_fields(metadata)

        assert result["user_metadata"] == {
            "custom1": "value1",
            "custom2": {"nested": "data"},
            "custom3": [1, 2, 3],
        }

    def test_extract_no_user_metadata(self):
        """Test extraction with only internal fields."""
        metadata = {
            "tags": ["test"],
            "importance": 0.6,
            "created_at": "2025-01-01T00:00:00",
        }
        result = extract_memory_fields(metadata)

        assert result["user_metadata"] == {}


class TestMergeMetadata:
    """Tests for merge_metadata function."""

    def test_merge_basic(self):
        """Test basic metadata merging."""
        base = {"tags": ["python"], "importance": 0.5}
        updates = {"tags": ["python", "ai"], "importance": 0.8}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert result["tags"] == ["python", "ai"]
        assert result["importance"] == 0.8

    def test_merge_with_timestamp(self):
        """Test merging adds updated_at timestamp."""
        base = {"tags": ["test"], "created_at": "2025-01-01T00:00:00"}
        updates = {"importance": 0.9}
        result = merge_metadata(base, updates, add_timestamp=True)

        assert "updated_at" in result
        assert result["created_at"] == "2025-01-01T00:00:00"
        assert result["importance"] == 0.9

    def test_merge_without_timestamp(self):
        """Test merging without adding timestamp."""
        base = {"tags": ["test"]}
        updates = {"importance": 0.7}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert "updated_at" not in result

    def test_merge_preserves_unupdated_fields(self):
        """Test that unupdated fields are preserved."""
        base = {
            "tags": ["test"],
            "importance": 0.5,
            "created_at": "2025-01-01T00:00:00",
            "custom": "value",
        }
        updates = {"importance": 0.9}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert result["tags"] == ["test"]
        assert result["importance"] == 0.9
        assert result["created_at"] == "2025-01-01T00:00:00"
        assert result["custom"] == "value"

    def test_merge_overwrites_existing_fields(self):
        """Test that updates overwrite existing values."""
        base = {"custom": "old_value", "other": "preserved"}
        updates = {"custom": "new_value"}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert result["custom"] == "new_value"
        assert result["other"] == "preserved"

    def test_merge_empty_updates(self):
        """Test merging with empty updates."""
        base = {"tags": ["test"], "importance": 0.5}
        updates = {}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert result == base

    def test_merge_adds_new_fields(self):
        """Test that new fields in updates are added."""
        base = {"tags": ["test"]}
        updates = {"importance": 0.8, "new_field": "value"}
        result = merge_metadata(base, updates, add_timestamp=False)

        assert result["tags"] == ["test"]
        assert result["importance"] == 0.8
        assert result["new_field"] == "value"


class TestBuildFullMetadata:
    """Tests for build_full_metadata function."""

    def test_build_with_all_params(self):
        """Test building metadata with all parameters."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        updated = datetime(2025, 1, 2, 12, 0, 0)

        result = build_full_metadata(
            tags=["python", "ai"],
            importance=0.8,
            user_metadata={"project": "kagura"},
            created_at=created,
            updated_at=updated,
        )

        assert result["tags"] == ["python", "ai"]
        assert result["importance"] == 0.8
        assert result["created_at"] == "2025-01-01T12:00:00"
        assert result["updated_at"] == "2025-01-02T12:00:00"
        assert result["project"] == "kagura"

    def test_build_with_defaults(self):
        """Test building metadata with default values."""
        result = build_full_metadata()

        assert result["tags"] == []
        assert result["importance"] == 0.5
        assert "created_at" in result  # Auto-generated
        assert result["updated_at"] is None

    def test_build_with_partial_params(self):
        """Test building with some parameters."""
        result = build_full_metadata(tags=["test"], importance=0.9)

        assert result["tags"] == ["test"]
        assert result["importance"] == 0.9
        assert "created_at" in result

    def test_build_with_string_timestamps(self):
        """Test building with string timestamps."""
        result = build_full_metadata(
            created_at="2025-01-01T12:00:00", updated_at="2025-01-02T12:00:00"
        )

        assert result["created_at"] == "2025-01-01T12:00:00"
        assert result["updated_at"] == "2025-01-02T12:00:00"

    def test_build_includes_user_metadata(self):
        """Test that user metadata is included in result."""
        result = build_full_metadata(
            user_metadata={"custom1": "value1", "custom2": {"nested": "data"}}
        )

        assert result["custom1"] == "value1"
        assert result["custom2"] == {"nested": "data"}

    def test_build_empty_user_metadata(self):
        """Test building with empty user metadata."""
        result = build_full_metadata(user_metadata={})

        assert "tags" in result
        assert "importance" in result
        # No extra user fields


class TestPrepareForChromadb:
    """Tests for prepare_for_chromadb function."""

    def test_prepare_with_lists_and_dicts(self):
        """Test preparation encodes lists and dicts."""
        metadata = {
            "tags": ["python", "ai"],
            "importance": 0.8,
            "config": {"model": "gpt-4"},
        }
        result = prepare_for_chromadb(metadata)

        assert isinstance(result["tags"], str)
        assert result["importance"] == 0.8
        assert isinstance(result["config"], str)

    def test_prepare_preserves_scalars(self):
        """Test that scalar values are preserved."""
        metadata = {
            "count": 42,
            "active": True,
            "name": "test",
            "score": 3.14,
        }
        result = prepare_for_chromadb(metadata)

        assert result == metadata

    def test_prepare_empty_metadata(self):
        """Test preparing empty metadata."""
        result = prepare_for_chromadb({})
        assert result == {}

    def test_prepare_standard_memory_metadata(self):
        """Test preparing standard memory metadata structure."""
        metadata = {
            "tags": ["tag1", "tag2"],
            "importance": 0.7,
            "created_at": "2025-01-01T12:00:00",
            "updated_at": "2025-01-02T12:00:00",
        }
        result = prepare_for_chromadb(metadata)

        assert isinstance(result["tags"], str)  # Encoded
        assert result["importance"] == 0.7  # Preserved
        assert result["created_at"] == "2025-01-01T12:00:00"  # Preserved
        assert result["updated_at"] == "2025-01-02T12:00:00"  # Preserved


class TestValidateImportance:
    """Tests for validate_importance function."""

    def test_validate_valid_float(self):
        """Test validation of valid float."""
        assert validate_importance(0.5) == 0.5

    def test_validate_valid_int(self):
        """Test validation of valid int."""
        assert validate_importance(1) == 1.0

    def test_validate_zero(self):
        """Test validation of zero."""
        assert validate_importance(0) == 0.0

    def test_validate_one(self):
        """Test validation of one."""
        assert validate_importance(1.0) == 1.0

    def test_validate_clamp_high(self):
        """Test that values >1.0 are clamped."""
        assert validate_importance(1.5) == 1.0
        assert validate_importance(10.0) == 1.0

    def test_validate_clamp_low(self):
        """Test that values <0.0 are clamped."""
        assert validate_importance(-0.5) == 0.0
        assert validate_importance(-10.0) == 0.0

    def test_validate_string_number(self):
        """Test validation of numeric string."""
        assert validate_importance("0.7") == 0.7

    def test_validate_invalid_string(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Importance must be a number"):
            validate_importance("invalid")

    def test_validate_none(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Importance must be a number"):
            validate_importance(None)

    def test_validate_list(self):
        """Test that list raises ValueError."""
        with pytest.raises(ValueError, match="Importance must be a number"):
            validate_importance([0.5])

    def test_validate_dict(self):
        """Test that dict raises ValueError."""
        with pytest.raises(ValueError, match="Importance must be a number"):
            validate_importance({"value": 0.5})


class TestMemoryMetadataType:
    """Tests for MemoryMetadata TypedDict."""

    def test_memory_metadata_structure(self):
        """Test that MemoryMetadata has expected structure."""
        metadata: MemoryMetadata = {
            "tags": ["test"],
            "importance": 0.5,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": None,
            "user_metadata": {"custom": "value"},
        }

        assert "tags" in metadata
        assert "importance" in metadata
        assert "created_at" in metadata
        assert "updated_at" in metadata
        assert "user_metadata" in metadata

    def test_memory_metadata_without_optional_user_metadata(self):
        """Test MemoryMetadata without optional user_metadata."""
        metadata: MemoryMetadata = {
            "tags": ["test"],
            "importance": 0.5,
            "created_at": None,
            "updated_at": None,
        }

        assert "tags" in metadata
        assert "importance" in metadata
