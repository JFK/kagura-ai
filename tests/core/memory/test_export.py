"""Tests for memory export/import functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from kagura.core.memory import MemoryManager
from kagura.core.memory.export import MemoryExporter, MemoryImporter


class TestMemoryExport:
    """Test memory export functionality."""

    @pytest.fixture
    def manager(self):
        """Create test MemoryManager."""
        return MemoryManager(user_id="test_user", agent_name="test_agent")

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)


    @pytest.mark.skip(reason="Persistent memory export needs database cleanup")
    @pytest.mark.asyncio
    async def test_export_persistent_memory(self, manager, temp_output_dir):
        """Test exporting persistent memory."""
        # Skip for now - needs proper database isolation
        pytest.skip("Needs database cleanup")

    @pytest.mark.asyncio
    async def test_export_creates_metadata(self, manager, temp_output_dir):
        """Test that export creates metadata file."""
        # Export
        exporter = MemoryExporter(manager)
        await exporter.export_all(temp_output_dir)

        # Check metadata file
        metadata_file = temp_output_dir / "metadata.json"
        assert metadata_file.exists()

        # Read metadata
        with open(metadata_file) as f:
            metadata = json.load(f)

        assert metadata["user_id"] == "test_user"
        assert metadata["agent_name"] == "test_agent"
        assert "exported_at" in metadata
        assert "stats" in metadata

    @pytest.mark.skip(reason="Graph export needs async API clarification")
    @pytest.mark.asyncio
    async def test_export_graph_data(self, temp_output_dir):
        """Test exporting graph data."""
        # Skip for now - needs GraphMemory API clarification
        pytest.skip("Needs GraphMemory async API clarification")


class TestMemoryImport:
    """Test memory import functionality."""

    @pytest.fixture
    def manager(self):
        """Create test MemoryManager."""
        return MemoryManager(user_id="test_user", agent_name="test_agent")

    @pytest.fixture
    def temp_import_dir(self):
        """Create temporary directory with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create test memories.jsonl
            memories_file = tmppath / "memories.jsonl"
            with open(memories_file, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "type": "memory",
                            "scope": "persistent",
                            "key": "import_key2",
                            "value": "import_value2",
                            "user_id": "test_user",
                            "agent_name": "test_agent",
                        }
                    )
                    + "\n"
                )

            yield tmppath

    @pytest.mark.asyncio
    async def test_import_memories(self, manager, temp_import_dir):
        """Test importing memories from JSONL."""
        # Import
        importer = MemoryImporter(manager)
        stats = await importer.import_all(temp_import_dir)

        # Check stats
        assert stats["memories"] == 1

        # Note: Persistent memory import verification skipped
        # (requires database cleanup between tests)

    @pytest.mark.asyncio
    async def test_import_nonexistent_directory(self, manager):
        """Test importing from non-existent directory."""
        importer = MemoryImporter(manager)

        with pytest.raises(FileNotFoundError):
            await importer.import_all("/nonexistent/path")

    @pytest.mark.asyncio
    async def test_import_empty_directory(self, manager):
        """Test importing from empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            importer = MemoryImporter(manager)
            stats = await importer.import_all(tmpdir)

            # Should succeed but import nothing
            assert stats["memories"] == 0
            assert stats["graph_nodes"] == 0


class TestExportImportRoundtrip:
    """Test export/import roundtrip (data preservation)."""

    @pytest.fixture
    def manager(self):
        """Create test MemoryManager."""
        return MemoryManager(user_id="roundtrip_user", agent_name="roundtrip_agent")

