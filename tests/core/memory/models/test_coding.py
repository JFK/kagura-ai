"""Tests for coding-specific memory data models."""

import pytest
from datetime import datetime

from kagura.core.memory.models.coding import (
    CodingPattern,
    CodingSession,
    DesignDecision,
    ErrorRecord,
    FileChangeRecord,
    ProjectContext,
)


class TestFileChangeRecord:
    """Test FileChangeRecord model."""

    def test_create_basic_record(self):
        """Test creating a basic file change record."""
        record = FileChangeRecord(
            file_path="src/auth.py",
            action="edit",
            diff="+ def validate_token(): ...",
            reason="Add token validation",
        )

        assert record.file_path == "src/auth.py"
        assert record.action == "edit"
        assert record.reason == "Add token validation"
        assert record.related_files == []
        assert isinstance(record.timestamp, datetime)
        assert record.session_id is None

    def test_with_related_files(self):
        """Test record with related files."""
        record = FileChangeRecord(
            file_path="src/auth.py",
            action="refactor",
            diff="Extracted validation logic",
            reason="Improve modularity",
            related_files=["src/middleware.py", "src/models/user.py"],
        )

        assert len(record.related_files) == 2
        assert "src/middleware.py" in record.related_files

    def test_with_line_range(self):
        """Test record with line range."""
        record = FileChangeRecord(
            file_path="src/utils.py",
            action="edit",
            diff="Refactored helper functions",
            reason="Code cleanup",
            line_range=(10, 50),
        )

        assert record.line_range == (10, 50)

    def test_validation_invalid_action(self):
        """Test validation rejects invalid action."""
        with pytest.raises(ValueError):
            FileChangeRecord(
                file_path="test.py",
                action="invalid_action",  # type: ignore
                diff="test",
                reason="test",
            )

    def test_action_synonym_mapping(self):
        """Test action synonyms are normalized correctly."""
        # Test "add" → "create"
        record1 = FileChangeRecord(
            file_path="new_file.py",
            action="add",  # type: ignore
            diff="New file added",
            reason="Initial creation",
        )
        assert record1.action == "create"

        # Test "modify" → "edit"
        record2 = FileChangeRecord(
            file_path="existing.py",
            action="modify",  # type: ignore
            diff="Modified code",
            reason="Bug fix",
        )
        assert record2.action == "edit"

        # Test "remove" → "delete"
        record3 = FileChangeRecord(
            file_path="old.py",
            action="remove",  # type: ignore
            diff="File removed",
            reason="Cleanup",
        )
        assert record3.action == "delete"

        # Test "move" → "rename"
        record4 = FileChangeRecord(
            file_path="relocated.py",
            action="move",  # type: ignore
            diff="File moved",
            reason="Reorganization",
        )
        assert record4.action == "rename"


class TestErrorRecord:
    """Test ErrorRecord model."""

    def test_create_basic_error(self):
        """Test creating a basic error record."""
        error = ErrorRecord(
            error_type="TypeError",
            message="can't compare offset-naive and offset-aware datetimes",
            stack_trace="Traceback:\n  File ...",
            file_path="src/auth.py",
            line_number=42,
        )

        assert error.error_type == "TypeError"
        assert error.line_number == 42
        assert error.frequency == 1
        assert error.resolved is False
        assert error.solution is None

    def test_with_solution(self):
        """Test error with solution."""
        error = ErrorRecord(
            error_type="TypeError",
            message="Error message",
            stack_trace="Stack trace",
            file_path="src/auth.py",
            line_number=42,
            solution="Use datetime.now(timezone.utc)",
        )

        assert error.solution is not None
        assert error.resolved is False  # Must be explicitly set

    def test_with_screenshot(self):
        """Test error with screenshot."""
        error = ErrorRecord(
            error_type="RuntimeError",
            message="Database error",
            stack_trace="Stack trace",
            file_path="src/db.py",
            line_number=15,
            screenshot_path="/path/to/screenshot.png",
        )

        assert error.screenshot_path == "/path/to/screenshot.png"
        assert error.screenshot_base64 is None

    def test_validation_negative_line_number(self):
        """Test validation rejects negative line numbers."""
        with pytest.raises(ValueError):
            ErrorRecord(
                error_type="Error",
                message="Test",
                stack_trace="Test",
                file_path="test.py",
                line_number=-1,
            )


class TestDesignDecision:
    """Test DesignDecision model."""

    def test_create_basic_decision(self):
        """Test creating a basic decision."""
        decision = DesignDecision(
            decision="Use JWT for auth",
            rationale="Stateless, scalable",
            impact="No session storage needed",
        )

        assert decision.decision == "Use JWT for auth"
        assert decision.confidence == 0.8  # Default
        assert decision.reviewed is False
        assert decision.alternatives == []

    def test_with_alternatives(self):
        """Test decision with alternatives."""
        decision = DesignDecision(
            decision="Use FastAPI",
            rationale="Modern, fast, async-first",
            impact="Better performance",
            alternatives=["Flask", "Django"],
            confidence=0.95,
        )

        assert len(decision.alternatives) == 2
        assert "Flask" in decision.alternatives
        assert decision.confidence == 0.95

    def test_validation_confidence_range(self):
        """Test validation enforces confidence range."""
        with pytest.raises(ValueError):
            DesignDecision(
                decision="Test",
                rationale="Test",
                impact="Test",
                confidence=1.5,  # > 1.0
            )


class TestCodingSession:
    """Test CodingSession model."""

    def test_create_session(self):
        """Test creating a coding session."""
        start = datetime.utcnow()
        session = CodingSession(
            session_id="session_123",
            user_id="dev_john",
            project_id="api-service",
            description="Implement authentication",
            start_time=start,
        )

        assert session.session_id == "session_123"
        assert session.is_active is True
        assert session.duration_minutes is None
        assert session.files_touched == []

    def test_session_with_end_time(self):
        """Test session with end time."""
        from datetime import timedelta

        start = datetime.utcnow()
        end = start + timedelta(minutes=45)

        session = CodingSession(
            session_id="session_123",
            user_id="dev_john",
            project_id="api-service",
            description="Bug fix",
            start_time=start,
            end_time=end,
        )

        assert session.is_active is False
        assert session.duration_minutes == pytest.approx(45.0, abs=0.1)

    def test_session_statistics(self):
        """Test session with statistics."""
        session = CodingSession(
            session_id="session_123",
            user_id="dev_john",
            project_id="api-service",
            description="Feature implementation",
            start_time=datetime.utcnow(),
            files_touched=["src/auth.py", "src/middleware.py"],
            errors_encountered=3,
            errors_fixed=2,
            decisions_made=1,
        )

        assert len(session.files_touched) == 2
        assert session.errors_encountered == 3
        assert session.errors_fixed == 2


class TestCodingPattern:
    """Test CodingPattern model."""

    def test_create_pattern(self):
        """Test creating a coding pattern."""
        pattern = CodingPattern(
            pattern_type="error_prone",
            description="Off-by-one errors in loops",
            frequency=5,
            confidence=0.85,
        )

        assert pattern.pattern_type == "error_prone"
        assert pattern.frequency == 5
        assert pattern.confidence == 0.85
        assert pattern.examples == []

    def test_with_examples_and_severity(self):
        """Test pattern with examples and severity."""
        pattern = CodingPattern(
            pattern_type="anti_pattern",
            description="Using global mutable state",
            frequency=3,
            confidence=0.9,
            examples=["utils.py:42", "helpers.py:15"],
            severity="high",
            recommendation="Use dependency injection instead",
        )

        assert len(pattern.examples) == 2
        assert pattern.severity == "high"
        assert pattern.recommendation is not None


class TestProjectContext:
    """Test ProjectContext model."""

    def test_create_context(self):
        """Test creating project context."""
        context = ProjectContext(
            project_id="api-service",
            summary="FastAPI-based REST API",
            recent_changes="Added JWT auth, refactored database layer",
            tech_stack=["FastAPI", "PostgreSQL", "Redis"],
        )

        assert context.project_id == "api-service"
        assert len(context.tech_stack) == 3
        assert context.architecture_style is None
        assert isinstance(context.generated_at, datetime)

    def test_with_full_details(self):
        """Test context with all details."""
        context = ProjectContext(
            project_id="api-service",
            summary="Microservices architecture",
            tech_stack=["FastAPI", "PostgreSQL"],
            architecture_style="Microservices",
            recent_changes="Auth implementation complete",
            active_issues=["Need to add rate limiting"],
            key_decisions=["Use JWT over sessions"],
            coding_patterns=["Heavy use of async/await"],
            token_count=1500,
        )

        assert context.architecture_style == "Microservices"
        assert len(context.active_issues) == 1
        assert context.token_count == 1500
