"""Shell command safety analysis system.

This module provides comprehensive safety checking for shell commands,
combining rule-based pattern matching with optional LLM-based analysis.

Key Features:
- Danger level classification (HIGH, MEDIUM, LOW, SAFE)
- Pattern-based detection (fast)
- LLM-based analysis (smart, optional)
- Risk explanation and safe alternatives
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class DangerLevel(str, Enum):
    """Command danger level classification."""

    HIGH = "HIGH"  # Irreversible damage, system-level risks
    MEDIUM = "MEDIUM"  # Data modification, reversible changes
    LOW = "LOW"  # Minor side effects, file creation
    SAFE = "SAFE"  # Read-only, harmless operations


@dataclass
class SafetyResult:
    """Result of command safety analysis.

    Attributes:
        level: Danger level classification
        reasoning: Explanation of why this level was assigned
        risks: List of specific risks identified
        safe_alternative: Suggested safer alternative command (if applicable)
        matched_patterns: Patterns that triggered the classification
    """

    level: DangerLevel
    reasoning: str
    risks: list[str]
    safe_alternative: str | None = None
    matched_patterns: list[str] | None = None


class RuleSafetyChecker:
    """Rule-based command safety checker using regex patterns."""

    # Danger patterns organized by severity
    DANGER_PATTERNS = {
        DangerLevel.HIGH: {
            "patterns": [
                r"rm\s+-rf\s+/\s*$",  # Delete root
                r"rm\s+-rf\s+/\w+\s*$",  # Delete top-level dir
                r"git\s+push.*--force.*\b(main|master)\b",  # Force push to main
                r"gh\s+pr\s+merge.*--admin",  # Admin merge bypass
                r"mkfs",  # Format filesystem
                r"dd\s+if=/dev/zero",  # Disk wipe
                r"sudo\s+(rm|dd|mkfs)",  # Sudo dangerous ops
                r":\(\)\{.*;\};:",  # Fork bomb
                r"chmod\s+-R\s+777\s+/",  # Chmod root
            ],
            "message": "🚨 CRITICAL DANGER: Irreversible system/data damage",
        },
        DangerLevel.MEDIUM: {
            "patterns": [
                r"gh\s+pr\s+merge(?!.*--dry-run)",  # PR merge
                r"gh\s+(issue|pr)\s+(delete|close)",  # Delete/close
                r"git\s+push(?!.*--dry-run)",  # Git push
                r"rm\s+-rf?\s+\S+",  # Recursive delete
                r"gh\s+(pr|issue)\s+create",  # Create PR/issue
                r"gh\s+release\s+create",  # Create release
                r">\s*/dev/",  # Redirect to device
                r"wget.*\|\s*sh",  # Pipe to shell
                r"curl.*\|\s*bash",  # Pipe to bash
            ],
            "message": "⚠️ WARNING: Data modification operation",
        },
        DangerLevel.LOW: {
            "patterns": [
                r"mkdir",  # Create directory
                r"touch",  # Create file
                r"echo.*>>?",  # Append to file
                r"cp\s+",  # Copy
                r"mv\s+",  # Move
            ],
            "message": "ℹ️ INFO: Minor file operations",
        },
    }

    # Safe command patterns (explicit whitelist)
    SAFE_PATTERNS = [
        r"^gh\s+(issue|pr|repo)\s+(view|list|diff|status)(?!.*delete)",
        r"^git\s+(status|log|diff|show|branch)(?!.*delete)",
        r"^ls\b",
        r"^pwd\b",
        r"^cat\b",
        r"^grep\b",
        r"^find\b",
        r"^which\b",
        r"^echo\s+[^>|]+$",  # Echo without redirection
    ]

    def check(self, command: str) -> SafetyResult:
        """Check command safety using pattern matching.

        Args:
            command: Shell command to analyze

        Returns:
            SafetyResult with classification and explanation
        """
        command_lower = command.strip()

        # Check HIGH danger patterns first
        for level in [DangerLevel.HIGH, DangerLevel.MEDIUM, DangerLevel.LOW]:
            pattern_config = self.DANGER_PATTERNS[level]
            for pattern in pattern_config["patterns"]:
                if re.search(pattern, command_lower, re.IGNORECASE):
                    risks = self._identify_risks(command_lower, level)
                    return SafetyResult(
                        level=level,
                        reasoning=pattern_config["message"],
                        risks=risks,
                        matched_patterns=[pattern],
                        safe_alternative=self._suggest_alternative(
                            command_lower, level
                        ),
                    )

        # Check SAFE patterns
        for pattern in self.SAFE_PATTERNS:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return SafetyResult(
                    level=DangerLevel.SAFE,
                    reasoning="✅ Read-only operation, no risks detected",
                    risks=[],
                    matched_patterns=[pattern],
                )

        # Default: MEDIUM (unknown command, proceed with caution)
        return SafetyResult(
            level=DangerLevel.MEDIUM,
            reasoning="⚠️ Unknown command pattern, proceed with caution",
            risks=["Unknown behavior, may have side effects"],
        )

    def _identify_risks(self, command: str, level: DangerLevel) -> list[str]:
        """Identify specific risks for a command."""
        risks = []

        if level == DangerLevel.HIGH:
            if "rm -rf /" in command:
                risks.append("Complete filesystem destruction")
            if "--force" in command and ("main" in command or "master" in command):
                risks.append("Rewrite production branch history")
            if "sudo" in command:
                risks.append("Elevated privileges, system-level changes")

        elif level == DangerLevel.MEDIUM:
            if "gh pr merge" in command:
                risks.append("Merge code without local review")
            if "git push" in command:
                risks.append("Publish local changes to remote")
            if "rm -rf" in command:
                risks.append("Recursive deletion, hard to recover")
            if "delete" in command or "close" in command:
                risks.append("Remove resources, may affect others")

        return risks if risks else ["Potential unintended side effects"]

    def _suggest_alternative(self, command: str, level: DangerLevel) -> str | None:
        """Suggest safer alternative for dangerous commands."""
        alternatives = {
            "gh pr merge": "gh pr review --approve && gh pr merge --squash",
            "git push --force": "git push --force-with-lease (safer than --force)",
            "rm -rf": "mv to trash or use specific paths (not wildcard)",
        }

        for pattern, alternative in alternatives.items():
            if pattern in command:
                return alternative

        return None


class CommandSafetyAnalyzer:
    """LLM-based command safety analyzer (optional, more intelligent)."""

    def __init__(self, enable_llm: bool = False):
        """Initialize safety analyzer.

        Args:
            enable_llm: Enable LLM-based analysis (requires API key)
        """
        self.enable_llm = enable_llm
        self.rule_checker = RuleSafetyChecker()

    async def analyze(
        self, command: str, context: dict[str, Any] | None = None
    ) -> SafetyResult:
        """Analyze command safety (LLM + Rules).

        Args:
            command: Shell command to analyze
            context: Additional context (project name, current branch, etc.)

        Returns:
            SafetyResult with detailed analysis
        """
        # Always run rule-based check first (fast)
        rule_result = self.rule_checker.check(command)

        # If HIGH danger or LLM disabled, return rule result
        if rule_result.level == DangerLevel.HIGH or not self.enable_llm:
            return rule_result

        # Optionally enhance with LLM analysis
        try:
            llm_result = await self._llm_analyze(command, context or {})
            # Combine results (take more conservative level)
            return self._merge_results(rule_result, llm_result)
        except Exception as e:
            logger.warning(f"LLM analysis failed, using rule-based result: {e}")
            return rule_result

    async def _llm_analyze(self, command: str, context: dict[str, Any]) -> SafetyResult:
        """LLM-based safety analysis (future implementation).

        Args:
            command: Command to analyze
            context: Execution context

        Returns:
            SafetyResult from LLM analysis
        """
        # TODO: Implement LLM-based analysis
        # - Use LiteLLM with fast model (gpt-4o-mini, claude-haiku)
        # - Structured output (JSON mode)
        # - Timeout (2s max)
        raise NotImplementedError("LLM-based analysis not yet implemented")

    def _merge_results(
        self, rule_result: SafetyResult, llm_result: SafetyResult
    ) -> SafetyResult:
        """Merge rule-based and LLM-based results (take more conservative)."""
        # Take higher danger level
        levels_order = [
            DangerLevel.SAFE,
            DangerLevel.LOW,
            DangerLevel.MEDIUM,
            DangerLevel.HIGH,
        ]
        rule_index = levels_order.index(rule_result.level)
        llm_index = levels_order.index(llm_result.level)

        if llm_index > rule_index:
            # LLM found higher danger
            return llm_result
        else:
            # Rule-based is more conservative or equal
            return rule_result


# Convenience function
async def check_command_safety(
    command: str, enable_llm: bool = False, context: dict[str, Any] | None = None
) -> SafetyResult:
    """Check command safety (convenience wrapper).

    Args:
        command: Shell command to check
        enable_llm: Use LLM analysis (slower but smarter)
        context: Execution context

    Returns:
        SafetyResult with safety classification
    """
    analyzer = CommandSafetyAnalyzer(enable_llm=enable_llm)
    return await analyzer.analyze(command, context)
