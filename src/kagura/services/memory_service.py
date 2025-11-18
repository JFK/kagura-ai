"""Memory service - Business logic for memory operations.

Provides CRUD operations for memory management with validation,
metadata construction, and consistent error handling.

Eliminates code duplication between MCP tools, API routes, and CLI commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from kagura.core.memory import MemoryManager
from kagura.services.base import BaseService


@dataclass
class MemoryResult:
    """Result of a memory operation.

    Attributes:
        key: Memory key
        success: Whether operation succeeded
        message: Human-readable message
        metadata: Additional operation metadata
    """

    key: str
    success: bool
    message: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Set metadata to empty dict if None."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """Result of a memory search operation.

    Attributes:
        results: List of search results
        count: Number of results
        metadata: Search metadata (e.g., query time, algorithm used)
    """

    results: list[dict[str, Any]]
    count: int
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Set metadata to empty dict if None."""
        if self.metadata is None:
            self.metadata = {}


class MemoryService(BaseService):
    """Business logic for memory operations.

    Provides validated, consistent memory CRUD operations that can be
    used by MCP tools, API routes, and CLI commands.

    Example:
        >>> memory_manager = MemoryManager("user_123", "global")
        >>> service = MemoryService(memory_manager)
        >>>
        >>> # Store memory
        >>> result = await service.store_memory(
        ...     key="user_preference",
        ...     value="Prefers dark mode",
        ...     tags=["preference", "ui"],
        ...     importance=0.7
        ... )
        >>> print(result.success)  # True
        >>>
        >>> # Search memories
        >>> search = await service.search_memory(
        ...     query="dark mode",
        ...     limit=10
        ... )
        >>> print(search.count)  # Number of results

    Args:
        memory_manager: MemoryManager instance for data access
    """

    def __init__(self, memory_manager: MemoryManager):
        """Initialize memory service.

        Args:
            memory_manager: MemoryManager instance for data access
        """
        super().__init__()
        self.memory = memory_manager
        self.logger.debug(
            f"Initialized MemoryService (user_id={memory_manager.user_id}, "
            f"agent_name={memory_manager.agent_name})"
        )

    def store_memory(
        self,
        key: str,
        value: str,
        tags: list[str] | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
        scope: str = "persistent",
    ) -> MemoryResult:
        """Store memory with validation and metadata construction.

        Args:
            key: Memory key (unique identifier)
            value: Memory content
            tags: Optional tags for categorization
            importance: Importance score (0.0-1.0, default: 0.5)
            metadata: Optional additional metadata
            scope: Storage scope ("persistent" or "working")

        Returns:
            MemoryResult with success status and metadata

        Raises:
            ValueError: If parameters are invalid

        Example:
            >>> result = await service.store_memory(
            ...     key="project_goal",
            ...     value="Build scalable AI memory system",
            ...     tags=["project", "goal"],
            ...     importance=0.9
            ... )
            >>> assert result.success
        """
        # Validation
        self.validate_required(key, "key")
        self.validate_required(value, "value")
        self.validate_range(importance, "importance", min_val=0.0, max_val=1.0)

        if scope not in ("persistent", "working"):
            raise ValueError(f"Invalid scope: {scope}. Must be 'persistent' or 'working'")

        # Build metadata
        now = datetime.now()
        full_metadata = {
            "tags": tags or [],
            "importance": importance,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "scope": scope,
        }

        # Merge user-provided metadata
        if metadata:
            full_metadata["metadata"] = metadata
            # Preserve top-level access for backwards compatibility
            full_metadata.update(metadata)

        # Store in appropriate scope
        try:
            # PersistentMemory.store() is synchronous and requires user_id
            self.memory.persistent.store(
                key=key,
                value=value,
                user_id=self.memory.user_id,
                agent_name=self.memory.agent_name,
                metadata=full_metadata,
            )

            # Note: Working memory was removed in v4.4.0
            # All memories are now persistent
            if scope == "working":
                self.logger.warning(
                    "Working memory scope requested but not available, using persistent"
                )

            self.logger.info(f"Stored memory: key={key}, scope={scope}")

            return MemoryResult(
                key=key,
                success=True,
                message=f"Memory stored successfully (scope: {scope})",
                metadata={
                    "scope": scope,
                    "importance": importance,
                    "tags": tags or [],
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return MemoryResult(
                key=key,
                success=False,
                message=f"Storage failed: {str(e)}",
            )

    def recall_memory(self, key: str) -> MemoryResult:
        """Recall memory by key.

        Args:
            key: Memory key to retrieve

        Returns:
            MemoryResult with retrieved value and metadata

        Example:
            >>> result = await service.recall_memory("project_goal")
            >>> print(result.metadata["value"])  # Retrieved content
        """
        self.validate_required(key, "key")

        try:
            # Recall from persistent memory (synchronous)
            value = self.memory.recall(key)

            if value:
                return MemoryResult(
                    key=key,
                    success=True,
                    message="Memory recalled successfully",
                    metadata={"value": value, "scope": "persistent"},
                )

            # Not found
            return MemoryResult(
                key=key,
                success=False,
                message=f"Memory not found: {key}",
            )

        except Exception as e:
            self.logger.error(f"Failed to recall memory: {e}")
            return MemoryResult(
                key=key,
                success=False,
                message=f"Recall failed: {str(e)}",
            )

    def delete_memory(self, key: str) -> MemoryResult:
        """Delete memory by key.

        Args:
            key: Memory key to delete

        Returns:
            MemoryResult with deletion status

        Example:
            >>> result = await service.delete_memory("old_preference")
            >>> assert result.success
        """
        self.validate_required(key, "key")

        try:
            # Delete from persistent memory (MemoryManager uses forget())
            self.memory.forget(key)

            # forget() doesn't return boolean, so we assume success
            deleted = True

            if deleted:
                self.logger.info(f"Deleted memory: key={key}")
                return MemoryResult(
                    key=key,
                    success=True,
                    message="Memory deleted successfully",
                )
            else:
                return MemoryResult(
                    key=key,
                    success=False,
                    message=f"Memory not found: {key}",
                )

        except Exception as e:
            self.logger.error(f"Failed to delete memory: {e}")
            return MemoryResult(
                key=key,
                success=False,
                message=f"Deletion failed: {str(e)}",
            )

    def search_memory(
        self,
        query: str,
        limit: int = 10,
        min_importance: float | None = None,
        tags: list[str] | None = None,
    ) -> SearchResult:
        """Search memories using hybrid search (BM25 + RAG).

        Args:
            query: Search query (natural language)
            limit: Maximum number of results (default: 10)
            min_importance: Optional minimum importance filter
            tags: Optional tag filter

        Returns:
            SearchResult with matching memories

        Example:
            >>> result = await service.search_memory(
            ...     query="dark mode preference",
            ...     limit=5,
            ...     min_importance=0.5
            ... )
            >>> for item in result.results:
            ...     print(item["key"], item["value"])
        """
        self.validate_required(query, "query")
        self.validate_range(limit, "limit", min_val=1, max_val=1000)

        if min_importance is not None:
            self.validate_range(
                min_importance, "min_importance", min_val=0.0, max_val=1.0
            )

        try:
            # Search using MemoryManager's search_memory method (synchronous)
            results = self.memory.search_memory(query, limit=limit)

            # Filter by importance if specified
            if min_importance is not None:
                results = [
                    r
                    for r in results
                    if r.get("metadata", {}).get("importance", 0) >= min_importance
                ]

            # Filter by tags if specified
            if tags:
                results = [
                    r
                    for r in results
                    if any(
                        tag in r.get("metadata", {}).get("tags", []) for tag in tags
                    )
                ]

            self.logger.info(f"Search completed: query='{query}', results={len(results)}")

            return SearchResult(
                results=results,
                count=len(results),
                metadata={
                    "query": query,
                    "limit": limit,
                    "min_importance": min_importance,
                    "tags": tags,
                },
            )

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return SearchResult(
                results=[],
                count=0,
                metadata={"error": str(e)},
            )

    def list_memories(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> SearchResult:
        """List all memories with pagination.

        Args:
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip (default: 0)

        Returns:
            SearchResult with all memories

        Example:
            >>> result = await service.list_memories(limit=50, offset=0)
            >>> print(f"Found {result.count} memories")
        """
        self.validate_range(limit, "limit", min_val=1, max_val=10000)
        self.validate_range(offset, "offset", min_val=0)

        try:
            # List from persistent memory (synchronous)
            all_memories = self.memory.persistent.fetch_all(
                self.memory.user_id, self.memory.agent_name
            )

            # Apply pagination
            paginated = all_memories[offset : offset + limit]

            return SearchResult(
                results=paginated,
                count=len(paginated),
                metadata={
                    "total": len(all_memories),
                    "limit": limit,
                    "offset": offset,
                },
            )

        except Exception as e:
            self.logger.error(f"List failed: {e}")
            return SearchResult(
                results=[],
                count=0,
                metadata={"error": str(e)},
            )

    def search_by_time_range(
        self,
        time_range: str,
        limit: int = 20,
        event_type: str | None = None,
    ) -> SearchResult:
        """Search memories by time range.

        Args:
            time_range: Time specification:
                - "last_24h" or "last_day": Last 24 hours
                - "last_week": Last 7 days
                - "last_month": Last 30 days
                - "YYYY-MM-DD": Specific date
                - "YYYY-MM-DD:YYYY-MM-DD": Date range
            limit: Maximum results (default: 20)
            event_type: Optional event type filter

        Returns:
            SearchResult with time-filtered memories
        """
        self.validate_required(time_range, "time_range")
        self.validate_range(limit, "limit", min_val=1, max_val=1000)

        # Parse time range
        now = datetime.utcnow()
        start_time: datetime | None = None
        end_time: datetime | None = None

        if time_range in ("last_24h", "last_day"):
            start_time = now - timedelta(days=1)
            end_time = now
        elif time_range == "last_week":
            start_time = now - timedelta(days=7)
            end_time = now
        elif time_range == "last_month":
            start_time = now - timedelta(days=30)
            end_time = now
        elif ":" in time_range:
            start_str, end_str = time_range.split(":")
            start_time = datetime.fromisoformat(start_str)
            end_time = datetime.fromisoformat(end_str)
        else:
            try:
                date = datetime.fromisoformat(time_range)
                start_time = date.replace(hour=0, minute=0, second=0)
                end_time = date.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise ValueError(f"Invalid time_range format: {time_range}")

        try:
            # Get all memories and filter by time
            all_memories = self.memory.persistent.fetch_all(
                self.memory.user_id, self.memory.agent_name
            )

            filtered = []
            for mem in all_memories:
                # Check timestamp
                created_at = mem.get("created_at")
                if created_at:
                    try:
                        ts_str = created_at.replace("Z", "+00:00")
                        ts = datetime.fromisoformat(str(ts_str))

                        if start_time and ts < start_time:
                            continue
                        if end_time and ts > end_time:
                            continue

                        # Filter by event type if specified
                        if event_type:
                            meta = mem.get("metadata", {})
                            if isinstance(meta, dict):
                                mem_event_type = meta.get("event_type", "")
                                if event_type.lower() not in str(mem_event_type).lower():
                                    continue

                        filtered.append(mem)
                    except (ValueError, AttributeError):
                        pass

            # Sort by timestamp (newest first) and limit
            filtered.sort(
                key=lambda m: m.get("created_at", ""), reverse=True
            )
            results = filtered[:limit]

            return SearchResult(
                results=results,
                count=len(results),
                metadata={
                    "time_range": time_range,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "event_type": event_type,
                },
            )

        except Exception as e:
            self.logger.error(f"Timeline search failed: {e}")
            return SearchResult(
                results=[],
                count=0,
                metadata={"error": str(e)},
            )

    def fuzzy_recall(
        self,
        key_pattern: str,
        similarity_threshold: float = 0.6,
        limit: int = 10,
    ) -> SearchResult:
        """Recall memories using fuzzy key matching.

        Args:
            key_pattern: Partial key or pattern
            similarity_threshold: Minimum similarity (0.0-1.0)
            limit: Maximum results

        Returns:
            SearchResult with fuzzy-matched memories
        """
        self.validate_required(key_pattern, "key_pattern")
        self.validate_range(similarity_threshold, "similarity_threshold", 0.0, 1.0)
        self.validate_range(limit, "limit", 1, 1000)

        try:
            from difflib import SequenceMatcher

            all_memories = self.memory.persistent.fetch_all(
                self.memory.user_id, self.memory.agent_name
            )

            matches = []
            key_pattern_lower = key_pattern.lower()

            for mem in all_memories:
                mem_key = mem.get("key", "")
                similarity = SequenceMatcher(
                    None, key_pattern_lower, mem_key.lower()
                ).ratio()

                if similarity >= similarity_threshold:
                    mem_result = dict(mem)
                    mem_result["similarity"] = similarity
                    matches.append(mem_result)

            matches.sort(key=lambda x: x["similarity"], reverse=True)
            results = matches[:limit]

            return SearchResult(
                results=results,
                count=len(results),
                metadata={
                    "key_pattern": key_pattern,
                    "similarity_threshold": similarity_threshold,
                },
            )

        except Exception as e:
            self.logger.error(f"Fuzzy recall failed: {e}")
            return SearchResult(
                results=[],
                count=0,
                metadata={"error": str(e)},
            )
