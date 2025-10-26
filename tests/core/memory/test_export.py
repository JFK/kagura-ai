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

    @pytest.mark.asyncio
    async def test_export_working_memory(self, manager, temp_output_dir):
        """Test exporting working memory."""
        # Add some working memory
        manager.working.set("key1", "value1")
        manager.working.set("key2", "value2")

        # Export
        exporter = MemoryExporter(manager)
        stats = await exporter.export_all(
            temp_output_dir,
            include_working=True,
            include_persistent=False,
            include_graph=False,
        )

        # Check stats
        assert stats["memories"] == 2

        # Check output file
        memories_file = temp_output_dir / "memories.jsonl"
        assert memories_file.exists()

        # Read and verify content
        with open(memories_file) as f:
            lines = f.readlines()

        assert len(lines) == 2

        # Parse first record
        record = json.loads(lines[0])
        assert record["type"] == "memory"
        assert record["scope"] == "working"
        assert record["key"] in ["key1", "key2"]
        assert record["user_id"] == "test_user"

    @pytest.mark.skip(reason="Persistent memory export needs database cleanup")
    @pytest.mark.asyncio
    async def test_export_persistent_memory(self, manager, temp_output_dir):
        """Test exporting persistent memory."""
        # Skip for now - needs proper database isolation
        pytest.skip("Needs database cleanup")

    @pytest.mark.asyncio
    async def test_export_creates_metadata(self, manager, temp_output_dir):
        """Test that export creates metadata file."""
        # Add some data
        manager.working.set("key", "value")

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
                            "scope": "working",
                            "key": "import_key1",
                            "value": "import_value1",
                            "user_id": "test_user",
                            "agent_name": "test_agent",
                        }
                    )
                    + "\n"
                )
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
        assert stats["memories"] == 2

        # Verify working memory
        assert manager.working.get("import_key1") == "import_value1"

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

    @pytest.mark.asyncio
    async def test_roundtrip_preserves_working_memory(self, manager):
        """Test that export → import preserves working memory."""
        # Add test data (working memory only for simpler test)
        manager.working.set("work_key1", "work_value1")
        manager.working.set("work_key2", "work_value2")

        # Export
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = MemoryExporter(manager)
            export_stats = await exporter.export_all(
                tmpdir,
                include_working=True,
                include_persistent=False,
                include_graph=False,
            )

            # Create new manager (fresh state)
            manager2 = MemoryManager(
                user_id="roundtrip_user",
                agent_name="roundtrip_agent",
            )

            # Import
            importer = MemoryImporter(manager2)
            import_stats = await importer.import_all(tmpdir)

            # Verify counts match
            assert import_stats["memories"] == export_stats["memories"]
            assert export_stats["memories"] == 2

            # Verify data matches
            assert manager2.working.get("work_key1") == "work_value1"
            assert manager2.working.get("work_key2") == "work_value2"
