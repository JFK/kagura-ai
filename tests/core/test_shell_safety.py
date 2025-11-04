"""Tests for shell command safety analysis."""

import pytest

from kagura.core.shell_safety import (
    CommandSafetyAnalyzer,
    DangerLevel,
    RuleSafetyChecker,
    SafetyResult,
    check_command_safety,
)


class TestRuleSafetyChecker:
    """Test suite for rule-based safety checker."""

    def test_high_danger_rm_rf_root(self):
        """Test detection of rm -rf / command."""
        checker = RuleSafetyChecker()
        result = checker.check("rm -rf /")

        assert result.level == DangerLevel.HIGH
        assert "CRITICAL" in result.reasoning

    def test_high_danger_force_push_main(self):
        """Test detection of force push to main."""
        checker = RuleSafetyChecker()
        result = checker.check("git push --force origin main")

        assert result.level == DangerLevel.HIGH
        assert len(result.risks) > 0

    def test_medium_danger_pr_merge(self):
        """Test detection of PR merge."""
        checker = RuleSafetyChecker()
        result = checker.check("gh pr merge 465")

        assert result.level == DangerLevel.MEDIUM
        assert "WARNING" in result.reasoning

    def test_medium_danger_git_push(self):
        """Test detection of git push."""
        checker = RuleSafetyChecker()
        result = checker.check("git push origin feature-branch")

        assert result.level == DangerLevel.MEDIUM

    def test_medium_danger_rm_rf(self):
        """Test detection of rm -rf."""
        checker = RuleSafetyChecker()
        result = checker.check("rm -rf build/")

        assert result.level == DangerLevel.MEDIUM
        assert "recursive deletion" in " ".join(result.risks).lower()

    def test_low_danger_mkdir(self):
        """Test detection of mkdir command."""
        checker = RuleSafetyChecker()
        result = checker.check("mkdir new_folder")

        assert result.level == DangerLevel.LOW

    def test_safe_gh_issue_view(self):
        """Test gh issue view is safe."""
        checker = RuleSafetyChecker()
        result = checker.check("gh issue view 348")

        assert result.level == DangerLevel.SAFE
        assert "Read-only" in result.reasoning

    def test_safe_git_status(self):
        """Test git status is safe."""
        checker = RuleSafetyChecker()
        result = checker.check("git status")

        assert result.level == DangerLevel.SAFE

    def test_safe_ls(self):
        """Test ls is safe."""
        checker = RuleSafetyChecker()
        result = checker.check("ls -la")

        assert result.level == DangerLevel.SAFE

    def test_safe_gh_pr_view(self):
        """Test gh pr view is safe."""
        checker = RuleSafetyChecker()
        result = checker.check("gh pr view 465")

        assert result.level == DangerLevel.SAFE

    def test_unknown_command_medium(self):
        """Test unknown commands default to MEDIUM."""
        checker = RuleSafetyChecker()
        result = checker.check("some_unknown_command --flag")

        # Should be cautious with unknown commands
        assert result.level == DangerLevel.MEDIUM
        assert "Unknown" in result.reasoning

    def test_safe_alternative_suggested(self):
        """Test safe alternatives are suggested."""
        checker = RuleSafetyChecker()
        result = checker.check("gh pr merge 123")

        # Should suggest safer approach
        assert result.safe_alternative is not None
        assert "review" in result.safe_alternative.lower()

    def test_matched_patterns_recorded(self):
        """Test matched patterns are recorded."""
        checker = RuleSafetyChecker()
        result = checker.check("gh issue view 348")

        assert result.matched_patterns is not None
        assert len(result.matched_patterns) > 0


class TestCommandSafetyAnalyzer:
    """Test suite for command safety analyzer."""

    @pytest.mark.asyncio
    async def test_analyze_safe_command(self):
        """Test analyzing safe command."""
        analyzer = CommandSafetyAnalyzer(enable_llm=False)
        result = await analyzer.analyze("ls -la")

        assert result.level == DangerLevel.SAFE

    @pytest.mark.asyncio
    async def test_analyze_high_danger(self):
        """Test analyzing high danger command."""
        analyzer = CommandSafetyAnalyzer(enable_llm=False)
        result = await analyzer.analyze("rm -rf /")

        assert result.level == DangerLevel.HIGH
        assert len(result.risks) > 0

    @pytest.mark.asyncio
    async def test_analyze_medium_danger(self):
        """Test analyzing medium danger command."""
        analyzer = CommandSafetyAnalyzer(enable_llm=False)
        result = await analyzer.analyze("git push origin main")

        assert result.level == DangerLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_llm_disabled_fallback(self):
        """Test LLM disabled falls back to rules."""
        analyzer = CommandSafetyAnalyzer(enable_llm=False)
        result = await analyzer.analyze("gh pr merge 123")

        # Should use rule-based check
        assert result.level == DangerLevel.MEDIUM


class TestConvenienceFunction:
    """Test suite for check_command_safety convenience function."""

    @pytest.mark.asyncio
    async def test_check_command_safety_safe(self):
        """Test convenience function for safe command."""
        result = await check_command_safety("git status")

        assert result.level == DangerLevel.SAFE

    @pytest.mark.asyncio
    async def test_check_command_safety_danger(self):
        """Test convenience function for dangerous command."""
        result = await check_command_safety("rm -rf /")

        assert result.level == DangerLevel.HIGH

    @pytest.mark.asyncio
    async def test_check_with_context(self):
        """Test safety check with context."""
        result = await check_command_safety(
            "gh pr merge 123", context={"repo": "kagura-ai", "branch": "main"}
        )

        assert result.level in [DangerLevel.MEDIUM, DangerLevel.HIGH]


class TestSafetyResult:
    """Test suite for SafetyResult dataclass."""

    def test_safety_result_creation(self):
        """Test creating SafetyResult."""
        result = SafetyResult(
            level=DangerLevel.SAFE,
            reasoning="Read-only operation",
            risks=[],
        )

        assert result.level == DangerLevel.SAFE
        assert result.reasoning == "Read-only operation"
        assert result.risks == []
        assert result.safe_alternative is None

    def test_safety_result_with_alternative(self):
        """Test SafetyResult with safe alternative."""
        result = SafetyResult(
            level=DangerLevel.HIGH,
            reasoning="Dangerous",
            risks=["Data loss"],
            safe_alternative="Use mv instead of rm",
        )

        assert result.safe_alternative == "Use mv instead of rm"
