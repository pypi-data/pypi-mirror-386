# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

from datetime import datetime, timedelta
from typing import Any

try:
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

    # Fallback classes for when Rich is not available
    class Live:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def update(self, *args):
            pass

    class Text:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def append(self, *args, **kwargs):
            pass

    class Console:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass


class ProgressTracker:
    """Real-time progress tracker for organization blocked PR checking operations."""

    def __init__(self, organization: str):
        """Initialize progress tracker for an organization blocked PR check.

        Args:
            organization: Name of the GitHub organization being checked
        """
        self.organization = organization
        self.start_time = datetime.now()
        self.console = Console() if RICH_AVAILABLE else None

        # Progress counters
        self.total_repositories = 0
        self.completed_repositories = 0
        self.current_repository = ""
        self.total_prs_analyzed = 0
        self.unmergeable_prs_found = 0
        self.current_operation = "Initializing..."
        self.errors_count = 0

        # Rate limiting tracking
        self.rate_limited = False
        self.rate_limit_reset_time: datetime | None = None

        # Rich Live display
        self.live: Live | None = None
        self.rich_available = RICH_AVAILABLE
        self.paused = False
        # Metrics (optional; displayed when provided)
        self.metrics_concurrency: int | None = None
        self.metrics_rps: float | None = None

        # Fallback for when Rich is not available
        self._last_display = ""

    def start(self):
        """Start the live progress display."""
        if not self.rich_available:
            return

        try:
            self.live = Live(
                self._generate_display_text(),
                console=self.console,
                refresh_per_second=2,
                transient=False,
            )
            if self.live:
                self.live.start()
        except Exception:
            # Fallback if Rich display fails (e.g., unsupported terminal)
            self.rich_available = False
            self.live = None

    def stop(self):
        """Stop the live progress display."""
        if self.live:
            try:
                self.live.stop()
            except Exception:
                # Ignore errors when stopping display
                pass
        # Ensure paused state is cleared when fully stopped
        self.paused = False

    def suspend(self):
        """Temporarily pause the live display to allow clean printing elsewhere."""
        if self.live and self.rich_available and not self.paused:
            try:
                self.live.stop()
            except Exception:
                pass
            self.paused = True

    def resume(self):
        """Resume the live display after it was suspended."""
        if self.rich_available and self.paused:
            try:
                self.live = Live(
                    self._generate_display_text(),
                    console=self.console,
                    refresh_per_second=2,
                    transient=False,
                )
                if self.live:
                    self.live.start()
            except Exception:
                # Fall back if restarting live display fails
                self.rich_available = False
                self.live = None
            finally:
                self.paused = False

    def update_metrics(self, concurrency: int, rps: float):
        """Update concurrency and RPS metrics (no-op since metrics are not displayed)."""
        pass

    def clear_metrics(self):
        """Clear the concurrency and RPS metrics (no-op since metrics are not displayed)."""
        pass

    def update_total_repositories(self, total: int):
        """Update the total number of repositories to check."""
        self.total_repositories = total
        self._refresh_display()

    def start_repository(self, repo_name: str):
        """Mark the start of checking a new repository."""
        self.current_repository = repo_name
        self.current_operation = f"Getting PRs from {repo_name}"
        self._refresh_display()

    def complete_repository(self, unmergeable_count: int = 0):
        """Mark completion of a repository check."""
        self.completed_repositories += 1
        self.unmergeable_prs_found += unmergeable_count
        self.current_operation = "Moving to next repository..."
        self._refresh_display()

    def update_operation(self, operation: str):
        """Update the current operation description."""
        self.current_operation = operation
        self._refresh_display()

    def analyze_pr(self, pr_number: int, repo_name: str):
        """Mark the start of analyzing a specific PR."""
        self.total_prs_analyzed += 1
        self.current_operation = f"Analyzing PR #{pr_number} in {repo_name}"
        self._refresh_display()

    def add_error(self):
        """Increment the error counter."""
        self.errors_count += 1
        self._refresh_display()

    def set_rate_limited(self, reset_time: datetime):
        """Mark that we're rate limited and show countdown."""
        self.rate_limited = True
        self.rate_limit_reset_time = reset_time
        self._refresh_display()

    def clear_rate_limited(self):
        """Clear the rate limited status."""
        self.rate_limited = False
        self.rate_limit_reset_time = None
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the live display if it's active."""
        if self.live and self.rich_available and not self.paused:
            try:
                self.live.update(self._generate_display_text())
            except Exception:
                # If Rich display fails, fall back to simple print
                self._fallback_display()
        elif not self.rich_available:
            self._fallback_display()

    def _generate_display_text(self) -> Text:
        """Generate the current progress display text."""
        if not self.rich_available:
            return Text()

        text = Text()

        # Main progress line
        if self.total_repositories > 0:
            progress_pct = (self.completed_repositories / self.total_repositories) * 100
            text.append("🔍 Checking ", style="bold blue")
            text.append(f"{self.organization} ", style="bold cyan")
            text.append(
                f"({self.completed_repositories}/{self.total_repositories} repos, ",
                style="white",
            )
            text.append(f"{progress_pct:.0f}%", style="green")
            text.append(") | ", style="white")
        else:
            text.append("🔍 Checking organization ", style="bold blue")
            text.append(f"{self.organization}", style="bold cyan")
            text.append(" (counting repositories...)", style="white")

        # Stats (only when repo count is known)
        if self.total_repositories > 0:
            text.append(f"{self.total_prs_analyzed} PRs analyzed | ", style="white")

            if self.unmergeable_prs_found > 0:
                text.append(f"{self.unmergeable_prs_found} unmergeable", style="red")
            else:
                text.append(f"{self.unmergeable_prs_found} unmergeable", style="green")

            if self.errors_count > 0:
                text.append(f" | {self.errors_count} errors", style="yellow")

        text.append("\n")

        # Current operation line
        if self.rate_limited and self.rate_limit_reset_time:
            remaining = self.rate_limit_reset_time - datetime.now()
            if remaining.total_seconds() > 0:
                text.append(
                    f"⏳ Rate limited - waiting {remaining.seconds}s", style="yellow"
                )
            else:
                text.append("⚡ Rate limit reset - resuming...", style="green")
        else:
            text.append(f"📋 {self.current_operation}", style="dim white")

        # Elapsed time
        elapsed = datetime.now() - self.start_time
        text.append(f"\n⏱️  Elapsed: {self._format_duration(elapsed)}", style="dim blue")

        return text

    def _fallback_display(self):
        """Fallback display method for when Rich is not available."""
        # Generate simple text display
        if self.total_repositories > 0:
            progress_pct = (self.completed_repositories / self.total_repositories) * 100
            progress_line = f"🔍 Checking {self.organization} ({self.completed_repositories}/{self.total_repositories} repos, {progress_pct:.0f}%) | {self.total_prs_analyzed} PRs analyzed | {self.unmergeable_prs_found} unmergeable"
            if self.errors_count > 0:
                progress_line += f" | {self.errors_count} errors"
        else:
            progress_line = f"🔍 Checking organization {self.organization} (counting repositories...)"

        operation_line = f"📋 {self.current_operation}"
        elapsed = datetime.now() - self.start_time
        time_line = f"⏱️  Elapsed: {self._format_duration(elapsed)}"

        current_display = f"{progress_line}\n{operation_line}\n{time_line}"

        # Only print if display has changed to avoid spam
        if current_display != self._last_display:
            print(f"\r{current_display}\n", end="", flush=True)
            self._last_display = current_display

    def _format_duration(self, duration: timedelta) -> str:
        """Format a duration for display."""
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60

        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the checking progress."""
        elapsed = datetime.now() - self.start_time

        return {
            "organization": self.organization,
            "total_repositories": self.total_repositories,
            "completed_repositories": self.completed_repositories,
            "total_prs_analyzed": self.total_prs_analyzed,
            "unmergeable_prs_found": self.unmergeable_prs_found,
            "errors_count": self.errors_count,
            "elapsed_time": self._format_duration(elapsed),
            "rate_limited": self.rate_limited,
        }


class MergeProgressTracker(ProgressTracker):
    """Specialized progress tracker for merge operations."""

    def __init__(self, organization: str):
        super().__init__(organization)
        self.similar_prs_found = 0
        self.prs_merged = 0
        self.merge_failures = 0

    def found_similar_pr(self):
        """Mark that a similar PR was found."""
        self.similar_prs_found += 1
        self._refresh_display()

    def merge_success(self):
        """Mark a successful merge."""
        self.prs_merged += 1
        self._refresh_display()

    def merge_failure(self):
        """Mark a failed merge."""
        self.merge_failures += 1
        self._refresh_display()

    def _generate_display_text(self) -> Text:
        """Generate merge-specific display text."""
        if not self.rich_available:
            return Text()

        text = Text()

        # Main progress line for merge operations
        if self.total_repositories > 0:
            progress_pct = (self.completed_repositories / self.total_repositories) * 100
            text.append("🔀 Searching for similar PRs ", style="bold blue")
            text.append(
                f"({self.completed_repositories}/{self.total_repositories} repos, ",
                style="white",
            )
            text.append(f"{progress_pct:.0f}%", style="green")
            text.append(") | ", style="white")
        else:
            # Special heading when examining the source PR before repo enumeration
            if "Getting source PR details" in (self.current_operation or ""):
                text.append("🔍 Examining source pull request in ", style="bold blue")
                text.append(f"{self.organization}", style="bold cyan")
            else:
                text.append("🔀 Analyzing PRs in ", style="bold blue")
                text.append(f"{self.organization}", style="bold cyan")

        # Stats for merge operations (only when repo count is known)
        if self.total_repositories > 0:
            text.append(f"{self.total_prs_analyzed} PRs analyzed", style="white")
            if self.errors_count > 0:
                text.append(f" | {self.errors_count} errors", style="yellow")

        text.append("\n")

        # Current operation line
        if self.rate_limited and self.rate_limit_reset_time:
            remaining = self.rate_limit_reset_time - datetime.now()
            if remaining.total_seconds() > 0:
                text.append(
                    f"⏳ Rate limited - waiting {remaining.seconds}s", style="yellow"
                )
            else:
                text.append("⚡ Rate limit reset - resuming...", style="green")
        else:
            text.append(f"📋 {self.current_operation}", style="dim white")

        # Elapsed time
        elapsed = datetime.now() - self.start_time
        text.append(f"\n⏱️  Elapsed: {self._format_duration(elapsed)}", style="dim blue")

        return text

    def get_summary(self) -> dict[str, Any]:
        """Get merge-specific summary."""
        summary = super().get_summary()
        summary.update(
            {
                "similar_prs_found": self.similar_prs_found,
                "prs_merged": self.prs_merged,
                "merge_failures": self.merge_failures,
            }
        )
        return summary


class DummyProgressTracker:
    """A no-op progress tracker for when progress display is disabled."""

    def __init__(self, organization: str):
        self.organization = organization

    def start(self):
        pass

    def stop(self):
        pass

    def update_total_repositories(self, total: int):
        pass

    def start_repository(self, repo_name: str):
        pass

    def complete_repository(self, unmergeable_count: int = 0):
        pass

    def update_operation(self, operation: str):
        pass

    def analyze_pr(self, pr_number: int, repo_name: str):
        pass

    def add_error(self):
        pass

    def set_rate_limited(self, reset_time: datetime):
        pass

    def clear_rate_limited(self):
        pass

    def found_similar_pr(self):
        pass

    def merge_success(self):
        pass

    def merge_failure(self):
        pass

    def get_summary(self) -> dict[str, Any]:
        return {"organization": self.organization}
