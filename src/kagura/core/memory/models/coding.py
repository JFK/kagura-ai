"""Coding-specific memory data models.

This module defines Pydantic models for tracking coding sessions, file changes,
errors, design decisions, and learned patterns.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class FileChangeRecord(BaseModel):
    """Record of a file modification during coding.

    Tracks what changed, why, and related context for cross-session understanding.

    Attributes:
        file_path: Absolute or relative path to the modified file
        action: Type of modification performed
        diff: Git-style diff or human-readable summary of changes
        reason: Explanation of why this change was made
        related_files: Other files affected by or related to this change
        timestamp: When the change occurred
        session_id: Optional ID of the coding session this belongs to
        line_range: Optional line numbers affected (start, end)
    """

    file_path: str = Field(..., description="Path to the modified file")
    action: Literal["create", "edit", "delete", "rename", "refactor", "test"] = Field(
        ..., description="Type of file modification"
    )
    diff: str = Field(..., description="Summary or diff of changes")
    reason: str = Field(..., description="Why this change was made")
    related_files: list[str] = Field(
        default_factory=list, description="Related or affected files"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When change occurred"
    )
    session_id: str | None = Field(None, description="Associated coding session ID")
    line_range: tuple[int, int] | None = Field(
        None, description="Line numbers affected (start, end)"
    )

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, v: str | None) -> str:
        """Normalize common action synonyms to valid action types.

        Args:
            v: Action value (may be synonym)

        Returns:
            Normalized action value

        Raises:
            ValueError: If action is invalid after normalization
        """
        if v is None:
            raise ValueError("action is required")

        # Map common synonyms to valid actions
        action_mapping = {
            "add": "create",
            "new": "create",
            "modify": "edit",
            "update": "edit",
            "change": "edit",
            "remove": "delete",
            "del": "delete",
            "move": "rename",
            "mv": "rename",
        }

        # Normalize: lowercase and map
        normalized = action_mapping.get(v.lower(), v.lower())

        # Validate against allowed values
        allowed = {"create", "edit", "delete", "rename", "refactor", "test"}
        if normalized not in allowed:
            raise ValueError(
                f"Invalid action '{v}'. Must be one of: {', '.join(sorted(allowed))}. "
                f"Common synonyms: add/new → create, modify/update/change → edit, "
                f"remove/del → delete, move/mv → rename"
            )

        return normalized


class ErrorRecord(BaseModel):
    """Record of an error encountered during coding.

    Captures error details, context, and solutions for pattern learning.

    Attributes:
        error_type: Classification of error (e.g., TypeError, SyntaxError)
        message: The error message text
        stack_trace: Full stack trace or relevant excerpts
        file_path: File where error occurred
        line_number: Line number where error occurred
        solution: How the error was resolved (if applicable)
        screenshot_path: Path to screenshot or base64-encoded image
        screenshot_base64: Base64-encoded image data
        frequency: Number of times this error pattern occurred
        timestamp: When error was encountered
        session_id: Associated coding session ID
        tags: Custom tags for categorization
        resolved: Whether the error has been fixed
    """

    error_type: str = Field(
        ..., description="Error classification (e.g., TypeError, CompilationError)"
    )
    message: str = Field(..., description="Error message text")
    stack_trace: str = Field(..., description="Stack trace or relevant excerpts")
    file_path: str = Field(..., description="File where error occurred")
    line_number: int = Field(..., ge=0, description="Line number of error")
    solution: str | None = Field(None, description="How error was resolved")
    screenshot_path: str | None = Field(None, description="Path to error screenshot")
    screenshot_base64: str | None = Field(
        None, description="Base64-encoded screenshot data"
    )
    frequency: int = Field(default=1, ge=1, description="Occurrence count")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When error occurred"
    )
    session_id: str | None = Field(None, description="Associated session ID")
    tags: list[str] = Field(
        default_factory=list, description="Custom categorization tags"
    )
    resolved: bool = Field(default=False, description="Whether error is fixed")


class DesignDecision(BaseModel):
    """Record of an architectural or design decision.

    Captures decision rationale, alternatives considered, and expected impact.

    Attributes:
        decision: Brief statement of the decision made
        rationale: Detailed reasoning behind the decision
        alternatives: Other options that were considered
        impact: Expected impact on the project
        tags: Categorization tags (e.g., 'architecture', 'library-choice')
        related_files: Files affected by this decision
        timestamp: When decision was made
        confidence: Confidence level in this decision (0.0-1.0)
        reviewed: Whether decision has been reviewed/validated
    """

    decision: str = Field(..., description="Brief decision statement")
    rationale: str = Field(..., description="Reasoning behind decision")
    alternatives: list[str] = Field(
        default_factory=list, description="Other options considered"
    )
    impact: str = Field(..., description="Expected project impact")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    related_files: list[str] = Field(
        default_factory=list, description="Files affected by decision"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When decision was made"
    )
    confidence: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Confidence level (0-1)"
    )
    reviewed: bool = Field(
        default=False, description="Whether decision has been reviewed"
    )


class CodingSession(BaseModel):
    """Record of a coding session.

    Tracks activities, outcomes, and context across a coherent work session.

    Attributes:
        session_id: Unique session identifier
        user_id: User performing the coding
        project_id: Project being worked on
        description: Brief description of session goals
        start_time: When session started
        end_time: When session ended (None if ongoing)
        files_touched: List of files modified during session
        errors_encountered: Count of errors encountered
        errors_fixed: Count of errors resolved
        decisions_made: Count of design decisions recorded
        summary: AI-generated or user-provided summary
        tags: Session categorization tags
        success: Whether session objectives were met
    """

    session_id: str = Field(..., description="Unique session ID")
    user_id: str = Field(..., description="User performing coding")
    project_id: str = Field(..., description="Project being worked on")
    description: str = Field(..., description="Session goals/description")
    start_time: datetime = Field(..., description="Session start time")
    end_time: datetime | None = Field(None, description="Session end time")
    files_touched: list[str] = Field(
        default_factory=list, description="Files modified in session"
    )
    errors_encountered: int = Field(
        default=0, ge=0, description="Errors encountered count"
    )
    errors_fixed: int = Field(default=0, ge=0, description="Errors fixed count")
    decisions_made: int = Field(
        default=0, ge=0, description="Design decisions made count"
    )
    summary: str | None = Field(None, description="Session summary")
    tags: list[str] = Field(
        default_factory=list, description="Session categorization tags"
    )
    success: bool | None = Field(None, description="Whether objectives were met")

    @property
    def duration_minutes(self) -> float | None:
        """Calculate session duration in minutes.

        Returns:
            Duration in minutes, or None if session is ongoing
        """
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() / 60.0

    @property
    def is_active(self) -> bool:
        """Check if session is currently active.

        Returns:
            True if session has not ended yet
        """
        return self.end_time is None


class CodingPattern(BaseModel):
    """Learned coding pattern from historical data.

    Represents recurring behaviors, preferences, or anti-patterns.

    Attributes:
        pattern_type: Category of pattern
        description: Detailed description of the pattern
        frequency: How often this pattern occurs
        confidence: Confidence in pattern validity (0.0-1.0)
        examples: Example instances of this pattern
        learned_at: When pattern was first identified
        last_seen: Most recent occurrence of pattern
        severity: For anti-patterns, how problematic (low/medium/high)
        recommendation: Suggested action regarding this pattern
    """

    pattern_type: Literal[
        "error_prone",
        "preferred_library",
        "naming_convention",
        "architecture",
        "testing_practice",
        "anti_pattern",
    ] = Field(..., description="Category of pattern")
    description: str = Field(..., description="Detailed pattern description")
    frequency: int = Field(default=1, ge=1, description="Occurrence count")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Pattern validity confidence"
    )
    examples: list[str] = Field(default_factory=list, description="Example instances")
    learned_at: datetime = Field(
        default_factory=datetime.utcnow, description="When pattern identified"
    )
    last_seen: datetime = Field(
        default_factory=datetime.utcnow, description="Most recent occurrence"
    )
    severity: Literal["low", "medium", "high"] | None = Field(
        None, description="Severity for anti-patterns"
    )
    recommendation: str | None = Field(None, description="Suggested action")


class ProjectContext(BaseModel):
    """Comprehensive project context summary.

    Aggregates key information about a project for AI assistants.

    Attributes:
        project_id: Project identifier
        summary: High-level project summary
        tech_stack: Technologies and libraries used
        architecture_style: Architectural pattern (e.g., MVC, microservices)
        recent_changes: Summary of recent file changes
        active_issues: Current problems or blockers
        key_decisions: Important design decisions made
        coding_patterns: Observed coding patterns
        generated_at: When this context was generated
        token_count: Approximate token count of full context
    """

    project_id: str = Field(..., description="Project identifier")
    summary: str = Field(..., description="High-level project summary")
    tech_stack: list[str] = Field(default_factory=list, description="Technologies used")
    architecture_style: str | None = Field(None, description="Architectural pattern")
    recent_changes: str = Field(..., description="Recent changes summary")
    active_issues: list[str] = Field(
        default_factory=list, description="Current blockers"
    )
    key_decisions: list[str] = Field(
        default_factory=list, description="Important decisions"
    )
    coding_patterns: list[str] = Field(
        default_factory=list, description="Observed patterns"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Context generation time"
    )
    token_count: int | None = Field(None, description="Approximate token count")
