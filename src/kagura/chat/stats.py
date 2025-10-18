"""Session statistics tracking for chat (v3.0)

Provides real-time token usage and cost visibility in chat sessions.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionStats:
    """Track LLM usage statistics for current chat session

    Tracks token usage, costs, and model breakdown for transparency.

    Example:
        >>> stats = SessionStats()
        >>> stats.track_call("gpt-5-mini", {"total": 100}, 1.5, 0.0001)
        >>> summary = stats.get_summary()
        >>> print(f"Total cost: ${summary['total_cost']:.4f}")
    """

    def __init__(self):
        """Initialize session stats tracking"""
        self.llm_calls: list[dict[str, Any]] = []
        self.start_time = datetime.now()

    def track_call(
        self, model: str, usage: dict[str, int], duration: float, cost: float
    ) -> None:
        """Track an LLM API call

        Args:
            model: Model name (e.g., "gpt-5-mini")
            usage: Token usage dict with 'prompt', 'completion', 'total' keys
            duration: Call duration in seconds
            cost: Call cost in USD

        Example:
            >>> stats.track_call(
            ...     "gpt-5-mini",
            ...     {"prompt": 50, "completion": 50, "total": 100},
            ...     1.5,
            ...     0.0001
            ... )
        """
        self.llm_calls.append(
            {
                "model": model,
                "tokens": usage,
                "duration": duration,
                "cost": cost,
                "timestamp": datetime.now(),
            }
        )

    def get_summary(self) -> dict[str, Any]:
        """Get session statistics summary

        Returns:
            Dict with:
            - total_calls: Number of LLM calls
            - total_tokens: Total tokens used
            - total_cost: Total cost in USD
            - models: Breakdown by model
            - duration: Session duration in seconds

        Example:
            >>> summary = stats.get_summary()
            >>> print(f"Calls: {summary['total_calls']}")
        """
        if not self.llm_calls:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "models": {},
                "duration": 0,
            }

        # Aggregate stats
        total_tokens = sum(call["tokens"]["total"] for call in self.llm_calls)
        total_cost = sum(call["cost"] for call in self.llm_calls)

        # Model breakdown
        model_stats: dict[str, Any] = defaultdict(
            lambda: {"calls": 0, "tokens": 0, "cost": 0.0}
        )

        for call in self.llm_calls:
            model = call["model"]
            model_stats[model]["calls"] += 1
            model_stats[model]["tokens"] += call["tokens"]["total"]
            model_stats[model]["cost"] += call["cost"]

        # Session duration
        duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "total_calls": len(self.llm_calls),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "models": dict(model_stats),
            "duration": duration,
        }

    def export_json(self, path: str) -> None:
        """Export stats to JSON file

        Args:
            path: Output file path

        Example:
            >>> stats.export_json("session_stats.json")
        """
        summary = self.get_summary()
        summary["calls_detail"] = self.llm_calls

        output_path = Path(path)
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

    def export_csv(self, path: str) -> None:
        """Export stats to CSV file

        Args:
            path: Output file path

        Example:
            >>> stats.export_csv("session_stats.csv")
        """
        output_path = Path(path)

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Timestamp",
                    "Model",
                    "Prompt Tokens",
                    "Completion Tokens",
                    "Total Tokens",
                    "Duration (s)",
                    "Cost ($)",
                ]
            )

            # Data rows
            for call in self.llm_calls:
                writer.writerow(
                    [
                        call["timestamp"].isoformat(),
                        call["model"],
                        call["tokens"].get("prompt", 0),
                        call["tokens"].get("completion", 0),
                        call["tokens"]["total"],
                        f"{call['duration']:.2f}",
                        f"{call['cost']:.6f}",
                    ]
                )


__all__ = ["SessionStats"]
