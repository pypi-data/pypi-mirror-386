"""Command-line interface for httptap.

This module provides the CLI entry point and argument parsing for the httptap tool.
Follows CLI best practices for error handling, exit codes, and user feedback.
"""

import argparse
import logging
import signal
import sys
from collections.abc import Mapping, Sequence
from typing import NoReturn

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from . import __version__
from .analyzer import HTTPTapAnalyzer
from .constants import (
    DEFAULT_TIMEOUT_SECONDS,
    EXIT_CODE_OK,
    EXIT_CODE_SOFTWARE,
    EXIT_CODE_TEMPFAIL,
    EXIT_CODE_USAGE,
    UNIX_SIGNAL_EXIT_OFFSET,
)
from .models import StepMetrics
from .render import OutputRenderer
from .utils import validate_url

# Exit codes (aligned with sysexits.h conventions)
# Fall back to canonical numeric equivalents when running on platforms
# that do not expose the EX_* constants (e.g., Windows).
EXIT_SUCCESS = EXIT_CODE_OK
EXIT_USAGE_ERROR = EXIT_CODE_USAGE
EXIT_NETWORK_ERROR = EXIT_CODE_TEMPFAIL
EXIT_FATAL_ERROR = EXIT_CODE_SOFTWARE


# Global console for error messages
console = Console(stderr=True)

# Configure logging with Rich
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_time=False, show_path=False)],
)
logger = logging.getLogger(__name__)


class RichHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Combined formatter that shows defaults while keeping raw layout."""


def _parse_headers(values: Sequence[str] | None) -> dict[str, str]:
    """Convert --header inputs into a case-preserving mapping."""
    if not values:
        return {}

    headers: dict[str, str] = {}
    canonical: dict[str, str] = {}
    for item in values:
        if ":" not in item:
            msg = f"Invalid header format: '{item}' (expected NAME:VALUE)"
            raise ValueError(msg)
        name, value = item.split(":", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            msg = f"Header name cannot be empty: '{item}'"
            raise ValueError(msg)
        lower = name.lower()
        key = canonical.get(lower, name)
        canonical.setdefault(lower, key)
        headers[key] = value
    return headers


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser.

    Returns:
        Configured ArgumentParser instance.

    """
    parser = argparse.ArgumentParser(
        prog="httptap",
        description="HTTP request visualizer (DNS → TCP → TLS → HTTP)",
        formatter_class=RichHelpFormatter,
        epilog=f"""
Examples:
  - Basic timing waterfall:
      httptap https://example.com
  - Follow redirect chains (up to 10 hops):
      httptap --follow http://example.com
  - Compact view with shorter timeout:
      httptap --compact --timeout 10 https://api.example.com
  - Metrics-only output and JSON export:
      httptap --metrics-only --json out/report.json https://example.com

Exit codes:
  {EXIT_SUCCESS:>3} (EX_OK)       : Success
  {EXIT_USAGE_ERROR:>3} (EX_USAGE)    : Invalid arguments
  {EXIT_FATAL_ERROR:>3} (EX_SOFTWARE) : Internal error
  {EXIT_NETWORK_ERROR:>3} (EX_TEMPFAIL) : Network/TLS error (partial output available)
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the httptap version and exit.",
    )

    parser.add_argument(
        "url",
        help="Target URL to analyze (must start with http:// or https://).",
    )

    request_group = parser.add_argument_group("Request options")
    request_group.add_argument(
        "--follow",
        action="store_true",
        help="Follow redirects until a non-3xx response is reached (max 10).",
    )
    request_group.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="Abort the request chain if total elapsed time exceeds SECONDS.",
    )
    request_group.add_argument(
        "--no-http2",
        action="store_true",
        help="Disable HTTP/2 negotiation and force HTTP/1.1 connections.",
    )
    request_group.add_argument(
        "-H",
        "--header",
        action="append",
        dest="headers",
        metavar="NAME:VALUE",
        help="Add a request header (repeatable).",
    )

    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "--compact",
        action="store_true",
        help="Print one summary line per step instead of the waterfall view.",
    )
    output_group.add_argument(
        "--metrics-only",
        action="store_true",
        help="Emit key=value metrics without Rich visuals or progress spinners.",
    )
    output_group.add_argument(
        "--json",
        metavar="PATH",
        help="Export the collected metrics, network, and response details to PATH.",
    )

    return parser


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum: int, _frame: object) -> NoReturn:
        """Handle interrupt signals gracefully.

        Args:
            signum: Signal number.
            _frame: Current stack frame (unused).

        """
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        sys.exit(UNIX_SIGNAL_EXIT_OFFSET + signum)  # Standard Unix convention

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def _execute_analysis(
    analyzer: HTTPTapAnalyzer,
    args: argparse.Namespace,
    headers: Mapping[str, str],
) -> list[StepMetrics]:
    """Execute HTTP analysis with optional progress reporting."""
    if args.metrics_only:
        return analyzer.analyze_url(args.url, headers=headers)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Analyzing {task.fields[url]}..."),
        console=Console(),
        transient=True,
    ) as progress:
        task = progress.add_task("analyze", url=args.url, total=None)
        steps = analyzer.analyze_url(args.url, headers=headers)
        progress.update(task, completed=True)
        return steps


def _export_results(
    renderer: OutputRenderer,
    steps: list[StepMetrics],
    args: argparse.Namespace,
) -> None:
    """Export analysis results when --json is provided."""
    if not args.json:
        return

    try:
        renderer.export_json(steps, args.url, args.json)
    except OSError as export_error:
        console.print(
            f"[yellow]⚠ Warning:[/yellow] Failed to export JSON: {export_error}",
        )


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command-line arguments with Rich formatting.

    Args:
        args: Parsed arguments.

    Raises:
        ValueError: If arguments are invalid.

    """
    # Validate URL
    if not validate_url(args.url):
        error_text = Text()
        error_text.append("Invalid URL: ", style="bold red")
        error_text.append(f"'{args.url}'", style="yellow")
        error_text.append("\n\nURLs must start with ", style="red")
        error_text.append("http://", style="cyan")
        error_text.append(" or ", style="red")
        error_text.append("https://", style="cyan")

        panel = Panel(
            error_text,
            title="[bold red]❌ Validation Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)
        msg = "Invalid URL"
        raise ValueError(msg)

    # Validate timeout
    if args.timeout <= 0:
        error_text = Text()
        error_text.append("Invalid timeout: ", style="bold red")
        error_text.append(f"{args.timeout}", style="yellow")
        error_text.append(" seconds\n\n", style="red")
        error_text.append("Timeout must be a positive number", style="red")

        panel = Panel(
            error_text,
            title="[bold red]❌ Validation Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)
        msg = f"Invalid timeout: {args.timeout}"
        raise ValueError(msg)

    # Validate headers
    try:
        args.headers = _parse_headers(getattr(args, "headers", None))
    except ValueError as exc:
        error_panel = Panel(
            str(exc),
            title="[bold red]❌ Header Error[/bold red]",
            border_style="red",
        )
        console.print(error_panel)
        raise ValueError(str(exc)) from exc


def determine_exit_code(steps: list[StepMetrics]) -> int:
    """Determine appropriate exit code based on analysis results.

    Args:
        steps: List of step metrics from analysis.

    Returns:
        Appropriate exit code.

    """
    if not steps:
        return EXIT_FATAL_ERROR

    has_errors = any(step.has_error for step in steps)
    if not has_errors:
        return EXIT_SUCCESS

    # Check if we have any partial data (network or response info)
    has_partial_data = any(step.network.ip or step.response.status for step in steps)

    return EXIT_NETWORK_ERROR if has_partial_data else EXIT_FATAL_ERROR


def main() -> int:
    """Run the CLI with Rich UI enhancements.

    Returns:
        Exit code (0=success, 64=bad args, 75=network issue, 70=internal error).

    """
    setup_signal_handlers()

    try:
        # Parse arguments
        parser = create_parser()
        args = parser.parse_args()

        # Validate arguments
        try:
            validate_arguments(args)
        except ValueError:
            return EXIT_USAGE_ERROR

        # Create analyzer
        analyzer = HTTPTapAnalyzer(
            follow_redirects=args.follow,
            timeout=args.timeout,
            http2=not args.no_http2,  # Correct: no_http2=True means http2=False
        )

        # Create renderer
        renderer = OutputRenderer(
            compact=args.compact,
            metrics_only=args.metrics_only,
        )

        # Perform analysis
        steps = _execute_analysis(analyzer, args, args.headers)

        # Render output
        renderer.render_analysis(steps, args.url)

        # Export JSON if requested
        _export_results(renderer, steps, args)

        # Determine exit code
        return determine_exit_code(steps)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user[/yellow]")
        return UNIX_SIGNAL_EXIT_OFFSET + signal.SIGINT

    except Exception as e:
        logger.exception("Unexpected error")

        error_panel = Panel(
            f"[red]{e}[/red]",
            title="[bold red]❌ Internal Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        )
        console.print(error_panel)
        return EXIT_FATAL_ERROR


if __name__ == "__main__":
    sys.exit(main())
