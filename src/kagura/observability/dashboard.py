"""Dashboard for visualizing agent execution telemetry."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .store import EventStore


class Dashboard:
    """Dashboard for visualizing telemetry data.

    Example:
        >>> from kagura.observability import EventStore, Dashboard
        >>> store = EventStore()
        >>> dashboard = Dashboard(store)
        >>> dashboard.show_live()  # Start live monitoring
    """

    def __init__(self, store: EventStore) -> None:
        """Initialize dashboard.

        Args:
            store: Event store to query telemetry data from
        """
        self.store = store
        self.console = Console()

    def show_live(
        self, agent_name: Optional[str] = None, refresh_rate: float = 1.0
    ) -> None:
        """Show live monitoring dashboard.

        Args:
            agent_name: Filter by agent name (optional)
            refresh_rate: Refresh interval in seconds
        """
        with Live(
            self._create_dashboard_layout(agent_name),
            console=self.console,
            refresh_per_second=1 / refresh_rate,
        ) as live:
            try:
                while True:
                    layout = self._create_dashboard_layout(agent_name)
                    live.update(layout)
                    time.sleep(refresh_rate)
            except KeyboardInterrupt:
                pass

    def show_list(
        self,
        agent_name: Optional[str] = None,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> None:
        """Show execution list.

        Args:
            agent_name: Filter by agent name
            limit: Maximum number of executions to show
            status: Filter by status (completed/failed)
        """
        executions = self.store.get_executions(
            agent_name=agent_name, status=status, limit=limit
        )

        if not executions:
            self.console.print("[yellow]No executions found[/yellow]")
            return

        table = self._create_execution_table(executions)
        self.console.print(table)

    def show_stats(
        self, agent_name: Optional[str] = None, since: Optional[float] = None
    ) -> None:
        """Show statistics summary.

        Args:
            agent_name: Filter by agent name
            since: Filter by start time (timestamp)
        """
        stats = self.store.get_summary_stats(agent_name=agent_name, since=since)

        # Get recent executions for detailed stats
        executions = self.store.get_executions(
            agent_name=agent_name, since=since, limit=1000
        )

        # Calculate additional stats
        total_cost = sum(
            exec.get("metrics", {}).get("total_cost", 0.0) for exec in executions
        )

        total_tokens = sum(
            exec.get("metrics", {}).get("total_tokens", 0) for exec in executions
        )

        llm_calls = sum(
            exec.get("metrics", {}).get("llm_calls", 0) for exec in executions
        )

        tool_calls = sum(
            exec.get("metrics", {}).get("tool_calls", 0) for exec in executions
        )

        # Create stats panel
        stats_text = Text()
        stats_text.append("📊 Summary Statistics\n\n", style="bold cyan")
        stats_text.append(
            f"Total Executions: {stats['total_executions']}\n", style="white"
        )
        stats_text.append(f"  • Completed: {stats['completed']}\n", style="green")
        stats_text.append(f"  • Failed: {stats['failed']}\n", style="red")
        stats_text.append(
            f"Avg Duration: {stats['avg_duration']:.2f}s\n", style="white"
        )
        stats_text.append(f"Total Cost: ${total_cost:.4f}\n", style="yellow")
        stats_text.append(f"Total Tokens: {total_tokens:,}\n", style="white")
        stats_text.append(f"LLM Calls: {llm_calls}\n", style="white")
        stats_text.append(f"Tool Calls: {tool_calls}\n", style="white")

        if stats["total_executions"] > 0:
            success_rate = stats["completed"] / stats["total_executions"] * 100
            stats_text.append(
                f"\nSuccess Rate: {success_rate:.1f}%\n",
                style="bold green" if success_rate > 90 else "bold yellow",
            )

        panel = Panel(stats_text, title="Statistics", border_style="cyan")
        self.console.print(panel)

    def show_trace(self, execution_id: str) -> None:
        """Show detailed trace for specific execution.

        Args:
            execution_id: Execution ID to show trace for
        """
        execution = self.store.get_execution(execution_id)

        if not execution:
            self.console.print(f"[red]Execution {execution_id} not found[/red]")
            return

        # Create trace tree
        agent_name = execution["agent_name"]
        tree = Tree(
            f"[bold cyan]Execution Trace: {agent_name} ({execution_id})[/bold cyan]"
        )

        # Add execution info
        info_branch = tree.add("[bold]Execution Info[/bold]")
        info_branch.add(f"Started: {self._format_timestamp(execution['started_at'])}")
        info_branch.add(f"Status: {self._format_status(execution['status'])}")
        info_branch.add(f"Duration: {execution.get('duration', 0):.2f}s")

        if execution.get("error"):
            info_branch.add(f"[red]Error: {execution['error']}[/red]")

        # Add metrics
        metrics = execution.get("metrics", {})
        if metrics:
            metrics_branch = tree.add("[bold]Metrics[/bold]")
            for key, value in metrics.items():
                if key == "total_cost":
                    metrics_branch.add(f"{key}: ${value:.4f}")
                else:
                    metrics_branch.add(f"{key}: {value}")

        # Add events timeline
        events = execution.get("events", [])
        if events:
            events_branch = tree.add(
                f"[bold]Events Timeline ({len(events)} events)[/bold]"
            )
            start_time = execution["started_at"]

            for event in events:
                elapsed = event["timestamp"] - start_time
                event_type = event["type"]
                data = event["data"]

                # Format event based on type
                if event_type == "llm_call":
                    event_str = (
                        f"[cyan]LLM Call[/cyan] "
                        f"({data['model']}) - "
                        f"{data['total_tokens']} tokens, "
                        f"${data['cost']:.4f}, "
                        f"{data['duration']:.2f}s"
                    )
                elif event_type == "tool_call":
                    event_str = (
                        f"[green]Tool Call[/green] "
                        f"({data['tool_name']}) - "
                        f"{data['duration']:.2f}s"
                    )
                elif event_type == "memory_operation":
                    event_str = (
                        f"[magenta]Memory Op[/magenta] "
                        f"({data['operation']}) - "
                        f"{data['duration']:.2f}s"
                    )
                else:
                    event_str = f"[white]{event_type}[/white]"

                events_branch.add(f"[{elapsed:.2f}s] {event_str}")

        self.console.print(tree)

    def show_cost_summary(
        self, since: Optional[float] = None, group_by: str = "agent"
    ) -> None:
        """Show cost summary.

        Args:
            since: Filter by start time (timestamp)
            group_by: Group by 'agent' or 'date'
        """
        executions = self.store.get_executions(since=since, limit=10000)

        if not executions:
            self.console.print("[yellow]No executions found[/yellow]")
            return

        # Group costs
        if group_by == "agent":
            self._show_cost_by_agent(executions)
        else:
            self._show_cost_by_date(executions)

    def _show_cost_by_agent(self, executions: list[dict[str, Any]]) -> None:
        """Show cost grouped by agent."""
        agent_costs: dict[str, dict[str, Any]] = {}

        for exec in executions:
            agent_name = exec["agent_name"]
            cost = exec.get("metrics", {}).get("total_cost", 0.0)
            tokens = exec.get("metrics", {}).get("total_tokens", 0)

            if agent_name not in agent_costs:
                agent_costs[agent_name] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "calls": 0,
                }

            agent_costs[agent_name]["cost"] += cost
            agent_costs[agent_name]["tokens"] += tokens
            agent_costs[agent_name]["calls"] += 1

        # Create table
        table = Table(title="Cost by Agent", show_header=True)
        table.add_column("Agent", style="cyan")
        table.add_column("Calls", justify="right", style="white")
        table.add_column("Tokens", justify="right", style="white")
        table.add_column("Cost", justify="right", style="yellow")

        total_cost = 0.0
        total_tokens = 0
        total_calls = 0

        for agent_name, data in sorted(
            agent_costs.items(), key=lambda x: x[1]["cost"], reverse=True
        ):
            table.add_row(
                agent_name,
                str(data["calls"]),
                f"{data['tokens']:,}",
                f"${data['cost']:.4f}",
            )
            total_cost += data["cost"]
            total_tokens += data["tokens"]
            total_calls += data["calls"]

        # Add total row
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{total_calls}[/bold]",
            f"[bold]{total_tokens:,}[/bold]",
            f"[bold yellow]${total_cost:.4f}[/bold yellow]",
        )

        self.console.print(table)

        # Estimate monthly cost
        if executions:
            oldest = min(e["started_at"] for e in executions)
            newest = max(e["started_at"] for e in executions)
            days = max(1, (newest - oldest) / 86400)
            daily_avg = total_cost / days
            monthly_estimate = daily_avg * 30

            self.console.print(
                f"\n[dim]Estimated monthly cost: ${monthly_estimate:.2f}[/dim]"
            )

    def _show_cost_by_date(self, executions: list[dict[str, Any]]) -> None:
        """Show cost grouped by date."""
        # Group by date
        date_costs: dict[str, float] = {}

        for exec in executions:
            date = datetime.fromtimestamp(exec["started_at"]).strftime("%Y-%m-%d")
            cost = exec.get("metrics", {}).get("total_cost", 0.0)

            if date not in date_costs:
                date_costs[date] = 0.0

            date_costs[date] += cost

        # Create table
        table = Table(title="Cost by Date", show_header=True)
        table.add_column("Date", style="cyan")
        table.add_column("Cost", justify="right", style="yellow")

        total_cost = 0.0

        for date in sorted(date_costs.keys(), reverse=True):
            cost = date_costs[date]
            table.add_row(date, f"${cost:.4f}")
            total_cost += cost

        # Add total row
        table.add_section()
        table.add_row(
            "[bold]Total[/bold]", f"[bold yellow]${total_cost:.4f}[/bold yellow]"
        )

        self.console.print(table)

    def _create_dashboard_layout(self, agent_name: Optional[str] = None) -> Layout:
        """Create Rich TUI dashboard layout for live monitoring.

        This creates a two-section layout used by show_live():
        1. Header: Summary statistics (total/completed/failed executions)
        2. Body: Recent activity table (last 15 executions)

        The layout is optimized for terminal display and auto-refresh.

        Args:
            agent_name: Filter executions by agent name (optional)

        Returns:
            Rich Layout object ready for Live rendering

        Note:
            Called repeatedly by show_live() for real-time updates.
            Keep queries lightweight for smooth refresh performance.
        """
        # Create root layout container
        layout = Layout()

        # Split into header (fixed 3 lines) and body (flexible)
        # This ensures header doesn't resize during refresh
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )

        # === Header Section: Summary Statistics ===
        # Fetch aggregated stats from EventStore
        stats = self.store.get_summary_stats(agent_name=agent_name)

        # Build styled header text with Rich Text markup
        header_text = Text()
        header_text.append("📊 Kagura Agent Monitor", style="bold cyan")
        if agent_name:
            header_text.append(f" - {agent_name}", style="bold yellow")
        header_text.append(
            f"\nTotal: {stats['total_executions']} | "
            f"Completed: {stats['completed']} | "
            f"Failed: {stats['failed']}",
            style="white",
        )

        # Wrap header in Panel with cyan border
        layout["header"].update(Panel(header_text, border_style="cyan", padding=(0, 1)))

        # === Body Section: Recent Activity Table ===
        # Fetch last 15 executions (limit for performance)
        executions = self.store.get_executions(agent_name=agent_name, limit=15)

        # Create formatted table with execution details
        activity_table = self._create_execution_table(executions)

        # Wrap table in Panel with title
        layout["body"].update(
            Panel(activity_table, title="Recent Activity", border_style="cyan")
        )

        return layout

    def _create_execution_table(self, executions: list[dict[str, Any]]) -> Table:
        """Create table of executions."""
        table = Table(show_header=True, header_style="bold")
        table.add_column("Time", style="dim")
        table.add_column("Agent", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Cost", justify="right", style="yellow")
        table.add_column("ID", style="dim")

        for exec in executions:
            # Extract model name from first LLM call event
            model_name = self._extract_model_name(exec)

            table.add_row(
                self._format_timestamp(exec["started_at"]),
                exec["agent_name"],
                model_name,
                self._format_status(exec.get("status", "unknown")),
                f"{exec.get('duration', 0):.2f}s",
                f"${exec.get('metrics', {}).get('total_cost', 0):.4f}",
                exec["id"][:12],
            )

        return table

    def _extract_model_name(self, execution: dict[str, Any]) -> str:
        """Extract model name from execution events.

        Args:
            execution: Execution dictionary

        Returns:
            Model name or "-" if not found
        """
        events = execution.get("events", [])
        for event in events:
            if event.get("type") == "llm_call":
                model = event.get("data", {}).get("model")
                if model:
                    return model
        return "-"

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp for display."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")

    def _format_status(self, status: str) -> str:
        """Format status with color."""
        if status == "completed":
            return "[green]✓ COMPLETED[/green]"
        elif status == "failed":
            return "[red]✗ FAILED[/red]"
        elif status == "running":
            return "[yellow]⋯ RUNNING[/yellow]"
        else:
            return f"[dim]{status}[/dim]"

    def __repr__(self) -> str:
        """String representation."""
        return f"Dashboard(store={self.store!r})"
