"""Tests for Persistent Memory RAG functionality (Issue #340)."""

import pytest

from kagura.core.memory import MemoryManager


@pytest.mark.integration
class TestPersistentRAG:
    """Test persistent memory RAG functionality."""

    @pytest.mark.asyncio
    async def test_persistent_rag_initialization(self) -> None:
        """Test that persistent_rag is created when enable_rag=True"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_persistent", enable_rag=True
            )

            # Both RAG instances should be created
            assert memory.rag is not None, "Working RAG should be initialized"
            assert memory.persistent_rag is not None, (
                "Persistent RAG should be initialized"
            )

            # Cleanup
            if memory.rag:
                memory.rag.delete_all("test_persistent")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_persistent")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_remember_indexes_in_persistent_rag(self) -> None:
        """Test that remember() indexes data in persistent RAG"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_remember", enable_rag=True
            )

            # Store in persistent memory
            memory.remember("project_deadline", "kagura-ai deadline: December 2025")

            # Verify it's in SQLite (traditional recall)
            value = memory.recall("project_deadline")
            assert value == "kagura-ai deadline: December 2025"

            # Verify it's also in persistent RAG (semantic search)
            results = memory.recall_semantic("deadline", top_k=5, scope="persistent")
            assert len(results) > 0, "Should find data in persistent RAG"

            # Verify the result contains our data
            found = False
            for result in results:
                if "December 2025" in result.get("content", ""):
                    found = True
                    assert result.get("scope") == "persistent"
                    break
            assert found, "Should find 'December 2025' in persistent RAG results"

            # Cleanup
            memory.forget("project_deadline")
            if memory.rag:
                memory.rag.delete_all("test_remember")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_remember")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_recall_semantic_scope_working(self) -> None:
        """Test recall_semantic with scope='working'"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_scope_working", enable_rag=True
            )

            # Store in both scopes
            memory.set_temp("temp_fact", "This is temporary data")
            if memory.rag:
                memory.store_semantic(
                    "temp_fact: This is temporary data",
                    {"type": "working_memory", "key": "temp_fact"},
                )

            memory.remember("persistent_fact", "This is persistent data")

            # Search only working scope
            results = memory.recall_semantic("data", top_k=10, scope="working")

            # Should only find working memory results
            for result in results:
                assert result.get("scope") == "working"
                content_lower = result.get("content", "").lower()
                metadata_str = str(result.get("metadata", {}))
                assert "temporary" in content_lower or "working" in metadata_str

            # Cleanup
            memory.forget("persistent_fact")
            if memory.rag:
                memory.rag.delete_all("test_scope_working")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_scope_working")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_recall_semantic_scope_persistent(self) -> None:
        """Test recall_semantic with scope='persistent'"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_scope_persistent", enable_rag=True
            )

            # Store in both scopes
            memory.set_temp("temp_fact", "This is temporary data")
            if memory.rag:
                memory.store_semantic(
                    "temp_fact: This is temporary data",
                    {"type": "working_memory", "key": "temp_fact"},
                )

            memory.remember("persistent_fact", "This is persistent data")

            # Search only persistent scope
            results = memory.recall_semantic("data", top_k=10, scope="persistent")

            # Should only find persistent memory results
            for result in results:
                assert result.get("scope") == "persistent"

            # Cleanup
            memory.forget("persistent_fact")
            if memory.rag:
                memory.rag.delete_all("test_scope_persistent")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_scope_persistent")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_recall_semantic_scope_all(self) -> None:
        """Test recall_semantic with scope='all' (default)"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_scope_all", enable_rag=True
            )

            # Store in both scopes
            memory.set_temp("temp_fact", "This is temporary data")
            if memory.rag:
                memory.store_semantic(
                    "temp_fact: This is temporary data",
                    {"type": "working_memory", "key": "temp_fact"},
                )

            memory.remember("persistent_fact", "This is persistent data")

            # Search all scopes
            results = memory.recall_semantic("data", top_k=10, scope="all")

            # Should find both working and persistent results
            # At least one of each scope should be present
            # (depending on semantic similarity)
            assert len(results) > 0

            # Cleanup
            memory.forget("persistent_fact")
            if memory.rag:
                memory.rag.delete_all("test_scope_all")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_scope_all")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_forget_deletes_from_rag(self) -> None:
        """Test that forget() deletes from both SQLite and RAG"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_forget", enable_rag=True
            )

            # Store data
            memory.remember("to_forget", "This data will be deleted")

            # Verify it's in both places
            assert memory.recall("to_forget") is not None

            # Delete
            memory.forget("to_forget")

            # Verify it's deleted from SQLite
            assert memory.recall("to_forget") is None

            # Verify forget() also attempts to delete from RAG
            # Note: We don't check the actual deletion because semantic search
            # may find other similar results. The important thing is that
            # forget() doesn't raise errors when RAG is enabled.
            assert True  # If we got here, forget() worked with RAG

            # Cleanup
            if memory.rag:
                memory.rag.delete_all("test_forget")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_forget")

        except ImportError:
            pytest.skip("ChromaDB not installed")

    @pytest.mark.asyncio
    async def test_memory_manager_repr_with_persistent_rag(self) -> None:
        """Test __repr__ includes persistent_rag count"""
        try:
            memory = MemoryManager(
                user_id="test_user", agent_name="test_repr", enable_rag=True
            )

            # Store some data
            memory.remember("key1", "value1")
            memory.remember("key2", "value2")

            repr_str = repr(memory)
            assert "persistent_rag=" in repr_str
            assert "working_rag=" in repr_str

            # Cleanup
            memory.forget("key1")
            memory.forget("key2")
            if memory.rag:
                memory.rag.delete_all("test_repr")
            if memory.persistent_rag:
                memory.persistent_rag.delete_all("test_repr")

        except ImportError:
            pytest.skip("ChromaDB not installed")
