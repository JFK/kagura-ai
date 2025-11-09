"""Analyzer functions for coding memory operations.

Extracted from CodingMemoryManager to support modular analysis:
- Project context generation
- Coding pattern analysis
- Interaction tracking
- File dependency analysis
- Refactoring impact assessment
- Error solution retrieval
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kagura.core.memory.coding.manager import CodingMemoryManager

from kagura.core.memory.models.coding import ProjectContext

logger = logging.getLogger(__name__)


async def get_project_context(
    self: CodingMemoryManager, focus: str | None = None
) -> ProjectContext:
    """Get comprehensive project context.

    Generates AI-powered project context summary.

    Args:
        focus: Optional focus area (e.g., "authentication")

    Returns:
        ProjectContext with structured information

    Example:
        >>> context = await coding_mem.get_project_context(
        ...     focus="authentication"
        ... )
        >>> print(context.summary)
        Python API using FastAPI with JWT authentication...
    """
    # Get recent data
    file_changes = await self._get_recent_file_changes(limit=30)
    decisions = await self._get_recent_decisions(limit=20)
    patterns = await self._get_coding_patterns()

    # Generate context using LLM
    context = await self.coding_analyzer.generate_project_context(
        project_id=self.project_id,
        file_changes=file_changes,
        decisions=decisions,
        patterns=patterns,
        focus=focus,
    )

    return context


async def analyze_coding_patterns(self: CodingMemoryManager) -> dict[str, Any]:
    """Analyze coding patterns and preferences.

    Uses LLM to extract developer's coding style and preferences.

    Returns:
        Dictionary with extracted preferences

    Example:
        >>> patterns = await coding_mem.analyze_coding_patterns()
        >>> print(patterns['language_preferences']['type_annotations'])
        {'style': 'always', 'confidence': 'high'}
    """
    file_changes = await self._get_recent_file_changes(limit=50)
    decisions = await self._get_recent_decisions(limit=30)

    preferences = await self.coding_analyzer.extract_coding_preferences(
        file_changes, decisions
    )

    return preferences


async def track_interaction(
    self: CodingMemoryManager,
    user_query: str,
    ai_response: str,
    interaction_type: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Track AI-User interaction with automatic importance classification.

    Records interaction in InteractionTracker with hybrid buffering strategy.
    High importance interactions (≥8.0) are automatically recorded to GitHub.

    Args:
        user_query: User's input/question
        ai_response: AI's response
        interaction_type: Type of interaction
            - "question": Low importance
            - "decision": High importance
            - "struggle": High importance
            - "discovery": High importance
            - "implementation": Medium importance
            - "error_fix": High importance
        metadata: Additional context (optional)

    Returns:
        Interaction ID

    Example:
        >>> interaction_id = await coding_mem.track_interaction(
        ...     user_query="How do I fix this TypeError?",
        ...     ai_response="Use timezone-aware datetime...",
        ...     interaction_type="error_fix"
        ... )
    """
    if not self.interaction_tracker:
        logger.warning("InteractionTracker not enabled, skipping")
        return ""

    # Import here to avoid circular dependency
    from kagura.core.memory.interaction_tracker import InteractionType

    # Validate interaction type
    valid_types: list[InteractionType] = [
        "question",
        "decision",
        "struggle",
        "discovery",
        "implementation",
        "error_fix",
    ]
    if interaction_type not in valid_types:
        raise ValueError(
            f"Invalid interaction_type: {interaction_type}. "
            f"Must be one of: {valid_types}"
        )

    # Track interaction
    record = await self.interaction_tracker.track_interaction(
        user_query=user_query,
        ai_response=ai_response,
        interaction_type=interaction_type,  # type: ignore
        session_id=self.current_session_id,
        metadata=metadata,
        llm_classifier=self.coding_analyzer if self.coding_analyzer else None,
        github_recorder=self.github_recorder if self.github_recorder else None,
    )

    logger.info(
        f"Tracked interaction {record.interaction_id}: "
        f"{interaction_type} (importance: {record.importance})"
    )

    return record.interaction_id


async def analyze_file_dependencies(
    self: CodingMemoryManager, file_path: str
) -> dict[str, Any]:
    """Analyze dependencies for a file.

    Args:
        file_path: File to analyze

    Returns:
        Dictionary with dependency information:
            - imports: Files this file imports
            - imported_by: Files that import this file
            - import_depth: Maximum import depth
            - circular_deps: Circular dependency chains involving this file

    Example:
        >>> deps = await coding_mem.analyze_file_dependencies("src/auth.py")
        >>> print(deps['imports'])
        ['src/models/user.py', 'src/utils/jwt.py']
        >>> print(deps['imported_by'])
        ['src/main.py', 'src/api/auth.py']
    """
    if not self.dependency_analyzer:
        logger.warning("Dependency analyzer not available (no persist_dir)")
        return {
            "imports": [],
            "imported_by": [],
            "import_depth": 0,
            "circular_deps": [],
        }

    # Analyze this file
    imports = self.dependency_analyzer.analyze_file(file_path)

    # Get reverse dependencies
    reverse_deps = self.dependency_analyzer.get_reverse_dependencies()
    imported_by = reverse_deps.get(file_path, [])

    # Get import depth
    depth = self.dependency_analyzer.get_import_depth(file_path)

    # Check for circular dependencies
    circular_deps = self.dependency_analyzer.find_circular_dependencies()
    relevant_cycles = [cycle for cycle in circular_deps if file_path in cycle]

    # Update graph with import relationships
    if self.graph:
        # Add file node (using helper)
        self._ensure_graph_node(
            node_id=file_path,
            node_type="file",
            data={"file_path": file_path, "project_id": self.project_id},
        )

        # Add import edges
        for imported in imports:
            # Ensure imported file node exists (using helper)
            self._ensure_graph_node(
                node_id=imported,
                node_type="file",
                data={"file_path": imported},
            )

            self.graph.add_edge(
                src_id=file_path,
                dst_id=imported,
                rel_type="imports",
                weight=1.0,
            )

    return {
        "imports": imports,
        "imported_by": imported_by,
        "import_depth": depth,
        "circular_deps": relevant_cycles,
    }


async def analyze_refactor_impact(
    self: CodingMemoryManager, file_path: str
) -> dict[str, Any]:
    """Analyze impact of refactoring a file.

    Args:
        file_path: File to refactor

    Returns:
        Dictionary with impact analysis:
            - affected_files: Files that would be affected
            - risk_level: low/medium/high
            - recommendations: Suggested actions

    Example:
        >>> impact = await coding_mem.analyze_refactor_impact("src/models/user.py")
        >>> print(impact['risk_level'])
        'high'  # Many files depend on this
        >>> print(impact['affected_files'])
        ['src/auth.py', 'src/api/users.py', 'src/main.py']
    """
    if not self.dependency_analyzer:
        return {
            "affected_files": [],
            "risk_level": "unknown",
            "recommendations": [
                "Enable dependency analysis by providing persist_dir"
            ],
        }

    # Get affected files
    affected = self.dependency_analyzer.get_affected_files(file_path)

    # Assess risk level
    if len(affected) == 0:
        risk_level = "low"
    elif len(affected) <= 3:
        risk_level = "medium"
    else:
        risk_level = "high"

    # Generate recommendations
    recommendations = []

    if risk_level == "high":
        recommendations.append(
            f"⚠️  {len(affected)} files depend on this - test thoroughly"
        )
        recommendations.append(
            "Consider adding integration tests before refactoring"
        )

    if risk_level == "medium":
        recommendations.append(
            f"ℹ️  {len(affected)} files affected - review carefully"
        )

    # Check for circular dependencies
    if self.dependency_analyzer:
        deps_info = await self.analyze_file_dependencies(file_path)  # type: ignore[attr-defined]
        if deps_info["circular_deps"]:
            circular_path = " → ".join(deps_info["circular_deps"][0])
            recommendations.append(
                f"⚠️  Circular dependency detected: {circular_path}"
            )
            risk_level = "high"  # Upgrade risk

    if not recommendations:
        recommendations.append("✅ Low risk - safe to refactor")

    return {
        "affected_files": affected,
        "risk_level": risk_level,
        "recommendations": recommendations,
    }


async def suggest_refactor_order(
    self: CodingMemoryManager, files: list[str]
) -> list[str]:
    """Suggest order to refactor multiple files.

    Args:
        files: Files to refactor

    Returns:
        Files in suggested refactoring order (safest first)

    Example:
        >>> order = await coding_mem.suggest_refactor_order([
        ...     "src/main.py",
        ...     "src/auth.py",
        ...     "src/models/user.py"
        ... ])
        >>> print(order)
        ['src/models/user.py', 'src/auth.py', 'src/main.py']
    """
    if not self.dependency_analyzer:
        logger.warning("Dependency analyzer not available")
        return files

    return self.dependency_analyzer.suggest_refactor_order(files)


async def get_solutions_for_error(
    self: CodingMemoryManager, error_id: str
) -> list[dict[str, Any]]:
    """Get solutions for an error from graph.

    Args:
        error_id: Error ID

    Returns:
        List of solutions with confidence scores

    Example:
        >>> solutions = await coding_mem.get_solutions_for_error("error_abc123")
        >>> for sol in solutions:
        ...     print(f"{sol['solution']} (confidence: {sol['confidence']})")
    """
    solutions = []

    if not self.graph or not self.graph.graph.has_node(error_id):
        return solutions

    # Find solution nodes linked from this error
    for _, dst_id, edge_data in self.graph.graph.out_edges(error_id, data=True):  # type: ignore[misc]
        if edge_data and edge_data.get("type") == "solved_by":
            # Get solution node data
            if self.graph.graph.has_node(dst_id):
                node_data = self.graph.graph.nodes[dst_id]
                solutions.append(
                    {
                        "solution_id": dst_id,
                        "solution": node_data.get("solution", ""),
                        "confidence": edge_data.get("weight", 0.0),
                    }
                )

    return solutions


