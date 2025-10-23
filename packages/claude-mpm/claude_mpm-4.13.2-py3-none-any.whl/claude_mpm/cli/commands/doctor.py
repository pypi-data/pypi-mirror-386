"""
Doctor command implementation for claude-mpm.

WHY: Provide a comprehensive diagnostic tool to help users identify and fix
common issues with their claude-mpm installation and configuration.

DESIGN DECISIONS:
- Use diagnostic runner for orchestration
- Support multiple output formats (terminal, JSON, markdown)
- Provide verbose mode for detailed diagnostics
- Future: Support --fix flag for automatic remediation
"""

import sys
from pathlib import Path

from ...services.diagnostics import DiagnosticRunner, DoctorReporter


def add_doctor_parser(subparsers):
    """Add doctor command parser.

    WHY: This command helps users diagnose and fix issues with their
    claude-mpm installation, providing clear actionable feedback.
    """
    parser = subparsers.add_parser(
        "doctor",
        aliases=["diagnose", "check-health"],
        help="Run comprehensive diagnostics on claude-mpm installation",
        description="Run comprehensive health checks on your claude-mpm installation and configuration",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed diagnostic information",
    )

    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    parser.add_argument(
        "--markdown", action="store_true", help="Output results in Markdown format"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to fix issues automatically (experimental)",
    )

    parser.add_argument(
        "--checks",
        nargs="+",
        choices=[
            "installation",
            "configuration",
            "filesystem",
            "claude",
            "agents",
            "mcp",
            "monitor",
            "common",
        ],
        help="Run only specific checks",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run checks in parallel for faster execution",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument("--output", "-o", type=Path, help="Save output to file")

    parser.add_argument(
        "--output-file",
        nargs="?",
        const=".",
        type=Path,
        default=None,
        help="Save report to file (default: mpm-doctor-report.md when used without path)",
    )

    parser.set_defaults(func=doctor_command)


def run_doctor(args):
    """Main entry point for doctor command (used by CLI).

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for warnings, 2 for errors)
    """
    return doctor_command(args)


def doctor_command(args):
    """Execute the doctor command.

    WHY: Provides a single entry point for system diagnostics, helping users
    quickly identify and resolve issues with their claude-mpm setup.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for warnings, 2 for errors)
    """
    # Configure logging
    from claude_mpm.core.logging_utils import get_logger

    logger = get_logger(__name__)

    # Handle output file parameter - support both --output and --output-file
    output_file = args.output or args.output_file
    if output_file is not None:
        # If output_file is specified without a path, use default
        if str(output_file) == ".":
            output_file = Path("mpm-doctor-report.md")
        elif not str(output_file).endswith((".md", ".json", ".txt")):
            # Add .md extension if no extension provided
            output_file = Path(str(output_file) + ".md")

    # Determine output format
    if args.json:
        output_format = "json"
    elif args.markdown:
        output_format = "markdown"
    elif output_file:
        # Force markdown format when writing to file (unless json specified)
        output_format = "json" if str(output_file).endswith(".json") else "markdown"
    else:
        output_format = "terminal"

    # Create diagnostic runner
    runner = DiagnosticRunner(verbose=args.verbose, fix=args.fix)

    # Run diagnostics
    try:
        if args.checks:
            # Run specific checks
            logger.info(f"Running specific checks: {', '.join(args.checks)}")
            summary = runner.run_specific_checks(args.checks)
        elif args.parallel:
            # Run all checks in parallel
            logger.info("Running diagnostics in parallel mode")
            summary = runner.run_diagnostics_parallel()
        else:
            # Run all checks sequentially
            logger.info("Running comprehensive diagnostics")
            summary = runner.run_diagnostics()

    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        print(f"\n❌ Diagnostic failed: {e!s}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 2

    # Create reporter
    reporter = DoctorReporter(use_color=not args.no_color, verbose=args.verbose)

    # Output results
    if output_file:
        # Save to file
        try:
            import sys

            original_stdout = sys.stdout
            with output_file.open("w") as f:
                sys.stdout = f
                reporter.report(summary, format=output_format)
            sys.stdout = original_stdout
            print(f"✅ Report saved to: {output_file}")

            # Also print brief summary to terminal
            if summary.error_count > 0:
                print(
                    f"❌ {summary.error_count} error(s) found - see report for details"
                )
            elif summary.warning_count > 0:
                print(
                    f"⚠️  {summary.warning_count} warning(s) found - see report for details"
                )
            else:
                print("✅ System is healthy!")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            print(f"❌ Failed to save report: {e!s}")
            # Still output to terminal
            reporter.report(summary, format=output_format)
    else:
        # Output to terminal
        reporter.report(summary, format=output_format)

    # Determine exit code based on results
    if summary.error_count > 0:
        return 2  # Errors found
    if summary.warning_count > 0:
        return 1  # Warnings found
    return 0  # All OK


# Optional: Standalone execution for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude MPM Doctor")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--checks", nargs="+")
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--output-file", type=Path)

    args = parser.parse_args()

    sys.exit(doctor_command(args))
