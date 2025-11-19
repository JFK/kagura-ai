"""Memory statistics and health reporting.

Provides insights into memory usage and health.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from kagura import tool
from kagura.mcp.tools.memory.common import get_memory_manager


@tool
async def memory_stats(
    user_id: str,
    agent_name: str = "global",
) -> str:
    """Get memory health report and statistics (read-only)

    Provides insights into memory usage without making any changes.
    Use this tool when:
    - User asks "how much do you remember?"
    - Checking memory health
    - Looking for cleanup opportunities

    💡 READ-ONLY: Does NOT delete or modify memories

    Args:
        user_id: User identifier
        agent_name: Agent identifier (default: "global")

    Returns:
        JSON with statistics and recommendations including:
        - total_memories: Total count
        - breakdown: {working, persistent}
        - analysis: {duplicates, old_90days, unused_30days, unused_90days, storage_mb}
          Note: storage_mb may be null if calculation fails
        - recommendations: List of suggestions
        - health_score: "excellent" | "good" | "fair"
    """
    logger = logging.getLogger(__name__)

    logger.debug(f"memory_stats: Starting for user={user_id}, agent={agent_name}")
    enable_rag = True
    memory = get_memory_manager(user_id, agent_name, enable_rag=enable_rag)
    logger.debug("memory_stats: Got memory manager")

    try:
        # Count memories
        logger.debug("memory_stats: Counting working memories")
        # Working memory removed in v4.4.0 - all memory is persistent
        working_keys_all = []
        working_count = 0
        logger.debug(f"memory_stats: Working count = {working_count} (v4.4.0: working memory removed)")

        logger.debug("memory_stats: Searching persistent memories")
        persistent_mems = memory.persistent.search("%", user_id, agent_name, limit=1000)
        persistent_count = len(persistent_mems)
        logger.debug(f"memory_stats: Persistent count = {persistent_count}")

        # Analyze duplicates
        logger.debug("memory_stats: Analyzing duplicates")
        working_keys = [k for k in working_keys_all if not k.startswith("_meta_")]
        duplicates = sum(
            1 for k in working_keys if any(m["key"] == k for m in persistent_mems)
        )
        logger.debug(f"memory_stats: Duplicates = {duplicates}")

        # Analyze old memories (>90 days)
        logger.debug("memory_stats: Analyzing old memories")
        old_threshold = datetime.now() - timedelta(days=90)
        old_count = 0
        for mem in persistent_mems:
            if mem.get("created_at"):
                try:
                    created_str = mem["created_at"].replace("Z", "+00:00")
                    created = datetime.fromisoformat(created_str)
                    if created < old_threshold:
                        old_count += 1
                except (ValueError, AttributeError):
                    pass

        # Analyze unused memories (Issue #411)
        logger.debug("memory_stats: Analyzing unused memories")
        unused_30_count = 0
        unused_90_count = 0
        now = datetime.now()

        for mem in persistent_mems:
            # Check last_accessed_at from metadata or direct field
            last_access = None
            metadata = mem.get("metadata")

            # Try metadata first (newer format)
            if metadata and isinstance(metadata, dict):
                last_access = metadata.get("last_accessed_at")

            # If not found, check if it's a direct field (v4.0.11+)
            if not last_access and "last_accessed_at" in mem:
                last_access = mem["last_accessed_at"]

            if last_access:
                try:
                    # Parse ISO format timestamp
                    last_access_str = (
                        last_access.replace("Z", "+00:00")
                        if isinstance(last_access, str)
                        else last_access
                    )
                    last_access_dt = datetime.fromisoformat(str(last_access_str))
                    days_since_access = (now - last_access_dt).days

                    if days_since_access > 90:
                        unused_90_count += 1
                    elif days_since_access > 30:
                        unused_30_count += 1
                except (ValueError, AttributeError, TypeError):
                    pass  # Skip malformed timestamps

        logger.debug(
            f"memory_stats: Unused counts - 30 days: {unused_30_count}, 90 days: {unused_90_count}"
        )

        # Tag distribution (both working and persistent)
        logger.debug("memory_stats: Analyzing tags")
        tag_counts: dict[str, int] = {}

        # Count tags from persistent memories
        for mem in persistent_mems:
            meta = mem.get("metadata")
            if meta and isinstance(meta, dict):
                tags = meta.get("tags", [])
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Count tags from working memories
        for key in working_keys:
            meta = memory.get_temp(f"_meta_{key}")
            if meta and isinstance(meta, dict):
                tags = meta.get("tags", [])
                # Working memory tags are already lists (not JSON strings)
                if isinstance(tags, str):
                    try:
                        tags = json.loads(tags)
                    except json.JSONDecodeError:
                        tags = []
                for tag in tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        logger.debug("memory_stats: Sorting tags")
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = dict(sorted_tags[:5])

        # Recommendations
        logger.debug("memory_stats: Generating recommendations")
        recs = []
        if duplicates:
            recs.append(f"{duplicates} duplicate keys - consider consolidating")
        if old_count > 10:
            recs.append(f"{old_count} memories >90 days - consider export")
        if unused_90_count > 10:
            recs.append(
                f"{unused_90_count} memories unused for 90+ days - consider cleanup"
            )
        if unused_30_count > 20:
            recs.append(
                f"{unused_30_count} memories unused for 30+ days - review if still needed"
            )
        if not recs:
            recs.append("Memory health looks good!")

        # Calculate storage size (Issue #411)
        logger.debug("memory_stats: Calculating storage size")
        try:
            storage_info = memory.get_storage_size()
            storage_mb = round(storage_info["total_mb"], 2)
            logger.debug(f"memory_stats: Storage = {storage_mb} MB")
        except Exception as e:
            logger.warning(f"Failed to calculate storage size: {e}")
            storage_mb = None

        # Health score
        logger.debug("memory_stats: Calculating health score")
        total = working_count + persistent_count
        health = "excellent" if total < 100 else "good" if total < 500 else "fair"

        stats = {
            "total_memories": total,
            "breakdown": {"working": working_count, "persistent": persistent_count},
            "analysis": {
                "duplicates": duplicates,
                "old_90days": old_count,
                "unused_30days": unused_30_count,
                "unused_90days": unused_90_count,
                "storage_mb": storage_mb,
            },
            "top_tags": top_tags,
            "recommendations": recs,
            "health_score": health,
        }

        logger.debug("memory_stats: Creating JSON response")
        result = json.dumps(stats, indent=2)
        logger.debug(f"memory_stats: Returning JSON (length={len(result)})")
        return result

    except Exception as e:
        return json.dumps({"error": str(e)})
