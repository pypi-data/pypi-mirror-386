"""Check command for human usage with batch processing."""

import asyncio
import os
import sys
from pathlib import Path

import click
import git

from zenable_mcp.exceptions import APIError, ConfigurationError
from zenable_mcp.exit_codes import ExitCode
from zenable_mcp.ide_context import IDEContextDetector, IDEType
from zenable_mcp.logging.command_logger import log_command
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.manager import record_command_usage
from zenable_mcp.utils.conformance_output import show_conformance_summary
from zenable_mcp.utils.files import (
    expand_file_patterns,
    filter_files_by_patterns,
    get_relative_paths,
)
from zenable_mcp.utils.git import get_branch_changed_files
from zenable_mcp.utils.mcp_client import (
    ZenableMCPClient,
    parse_conformance_results,
)
from zenable_mcp.utils.zenable_config import filter_files_by_zenable_config


def detect_files_from_ide_context(base_path: Path | None) -> list[Path]:
    """
    Auto-detect files from IDE context when no patterns are provided.

    Returns:
        List of file paths detected from IDE context
    """
    detector = IDEContextDetector()
    ide_type = detector.detect_context()

    if ide_type.value != "unknown":
        echo(f"Detected {ide_type.value} IDE context", persona=Persona.POWER_USER)

    env_files = detector.get_file_paths()
    if not env_files:
        echo(
            "No files detected from IDE context. This could mean:",
            persona=Persona.POWER_USER,
        )
        echo("  1. No modified files in the git repository", persona=Persona.POWER_USER)
        echo(
            "  2. All modified files are filtered by .gitignore",
            persona=Persona.POWER_USER,
        )
        echo(
            "  3. All modified files are filtered by Zenable config",
            persona=Persona.POWER_USER,
        )
        echo("  4. Not in a git repository", persona=Persona.POWER_USER)
        echo(
            "Error: No files specified and none detected from IDE context",
            err=True,
            log=False,
        )
        echo(
            "Please provide file patterns or check from a git repository",
            err=True,
            log=False,
        )
        sys.exit(ExitCode.NO_FILES_SPECIFIED)

    # Check if we're using the fallback mechanism (most recently edited file)
    if ide_type == IDEType.UNKNOWN:
        echo(
            f"Auto-detected {len(env_files)} file(s) using the fallback mechanism of last modified file",
            persona=Persona.POWER_USER,
        )
        # Files are already filtered by zenable config in the fallback mechanism
        file_paths = []
        for file_str in env_files:
            file_path = Path(file_str)
            if file_path.exists():
                file_paths.append(file_path)
            else:
                echo(
                    f"Warning: File from IDE context not found: {file_str}",
                    err=True,
                    log=False,
                )
        return file_paths
    else:
        echo(
            f"Auto-detected {len(env_files)} file(s) from {ide_type.value} IDE context",
            persona=Persona.POWER_USER,
        )
        # Convert environment file paths to Path objects
        env_file_paths = []
        for file_str in env_files:
            file_path = Path(file_str)
            if file_path.exists():
                env_file_paths.append(file_path)
            else:
                echo(
                    f"Warning: File from IDE context not found: {file_str}",
                    err=True,
                    log=False,
                )

        # Filter based on zenable config using the shared utility
        files_before_filter = len(env_file_paths)
        file_paths = filter_files_by_zenable_config(env_file_paths)
        filtered_count = files_before_filter - len(file_paths)

        if filtered_count > 0:
            echo(
                f"Filtered out {filtered_count} file(s) based on Zenable config skip patterns",
                persona=Persona.POWER_USER,
            )

        # If all files were filtered out, provide a helpful message
        if not file_paths and filtered_count > 0:
            echo(
                "All files from IDE context were filtered out by Zenable config skip patterns",
                log=False,
            )
            echo("No files to check.", log=False)
            sys.exit(ExitCode.SUCCESS)

        return file_paths


def create_header(*lines: str, padding: int = 8) -> str:
    """
    Create a centered header with equal signs.

    Args:
        lines: Text lines to display in the header
        padding: Number of spaces/equals on each side (default 8)

    Returns:
        Formatted header string
    """
    if not lines:
        return ""

    # Find the longest line
    max_length = max(len(line) for line in lines)

    # Total width is padding + max_length + padding
    total_width = padding * 2 + max_length

    # Build the header
    header_lines = []
    header_lines.append("=" * total_width)

    for line in lines:
        # Center each line within the available space
        centered = line.center(max_length)
        # Add padding on both sides
        header_lines.append(" " * padding + centered + " " * padding)

    header_lines.append("=" * total_width)

    return "\n".join(header_lines)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("patterns", nargs=-1, required=False)
@click.option(
    "--exclude",
    multiple=True,
    help="Patterns to exclude from checking",
)
@click.option(
    "--base-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for pattern matching (defaults to current directory)",
)
@click.option(
    "--branch",
    is_flag=True,
    help="Check all files changed on the current branch compared to the base branch",
)
@click.option(
    "--base-branch",
    default=lambda: os.getenv("ZENABLE_CHECK_BASE_BRANCH", "main"),
    help="Base branch to compare against when using --branch (default: $ZENABLE_CHECK_BASE_BRANCH or 'main')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show which files would be sent without actually checking them",
)
@click.pass_context
@log_command
def check(ctx, patterns, exclude, base_path, branch, base_branch, dry_run):
    """Check the provided files against your conformance tests

    Automatically detects files from IDE context when no patterns are provided.
    Supports glob patterns like **/*.py to check all Python files recursively.
    Files are processed in batches of 5 for optimal performance.

    \b
    Examples:
      # Check a single file
      zenable-mcp check example.py
    \b
      # Check all Python files recursively
      zenable-mcp check '**/*.py'
    \b
      # Check multiple patterns
      zenable-mcp check 'src/**/*.js' 'tests/**/*.js'
    \b
      # Exclude test files from checking
      zenable-mcp check '**/*.py' --exclude '**/test_*.py'
    \b
      # Specify base directory for pattern matching
      zenable-mcp check '*.py' --base-path ./src
    \b
      # Check all files changed on current branch compared to main
      zenable-mcp check --branch
    \b
      # Check all files changed on current branch compared to develop
      zenable-mcp check --branch --base-branch develop
    \b
      # Check only Python src files changed on current branch
      zenable-mcp check --branch '**/*.py' --exclude '**/test_*.py'
    \b
      # Dry run to see which files would be checked
      zenable-mcp check '**/*.py' --dry-run
    """
    # Display welcome header
    welcome_header = create_header(
        "Welcome to Zenable", "Production-Grade AI Coding Tools"
    )
    echo("\n" + welcome_header + "\n")
    echo("Detecting files...", log=False)

    # Determine which files to check
    file_paths = []

    if branch:
        # Check all files changed on the current branch
        echo(
            f"Checking all files changed on current branch compared to {base_branch}",
            persona=Persona.POWER_USER,
        )
        changed_files = get_branch_changed_files(base_path, base_branch)

        if not changed_files:
            echo(
                f"No files changed on current branch compared to {base_branch}",
                err=True,
            )
            sys.exit(ExitCode.NO_FILES_FOUND)

        # Already Path objects from get_branch_changed_files
        file_paths = changed_files

        # Apply pattern filters if specified (using the same patterns and exclude as regular mode)
        if patterns or exclude:
            files_before_pattern_filter = len(file_paths)
            file_paths = filter_files_by_patterns(
                file_paths,
                patterns=list(patterns) if patterns else None,
                exclude_patterns=list(exclude) if exclude else None,
                handler_name="--branch",
            )
            pattern_filtered_count = files_before_pattern_filter - len(file_paths)

            if pattern_filtered_count > 0:
                echo(
                    f"Filtered out {pattern_filtered_count} file(s) based on patterns",
                    persona=Persona.POWER_USER,
                )

        # Apply Zenable config filtering
        files_before_filter = len(file_paths)
        file_paths = filter_files_by_zenable_config(file_paths)
        filtered_count = files_before_filter - len(file_paths)

        if filtered_count > 0:
            echo(
                f"Filtered out {filtered_count} file(s) based on Zenable config skip patterns",
                persona=Persona.POWER_USER,
            )

        if not file_paths:
            if patterns or exclude:
                echo(
                    "All branch files were filtered out by patterns and/or Zenable config",
                    persona=Persona.POWER_USER,
                    log=False,
                )
            else:
                echo(
                    "All branch files were filtered out by Zenable config skip patterns",
                    persona=Persona.POWER_USER,
                    log=False,
                )
            echo("No files to check.", log=False)
            sys.exit(ExitCode.SUCCESS)

    elif not patterns:
        # Auto-detect from IDE context
        file_paths = detect_files_from_ide_context(base_path)
    else:
        # Use provided CLI patterns
        try:
            file_paths = expand_file_patterns(
                list(patterns),
                base_path=base_path,
                exclude_patterns=list(exclude) if exclude else None,
            )
        except ValueError as e:
            # Dangerous patterns or invalid patterns
            echo(f"Invalid file pattern: {e}", err=True)
            sys.exit(ExitCode.NO_FILES_FOUND)
        except (OSError, IOError) as e:
            # File system access errors
            echo(f"File system error: {e}", err=True)
            sys.exit(ExitCode.NO_FILES_FOUND)
        except Exception as e:
            # Unexpected errors - log with more context
            echo(
                f"Unexpected error expanding file patterns, please report this to https://zenable.io/feedback: {e}",
                err=True,
            )
            sys.exit(ExitCode.NO_FILES_FOUND)

    if not file_paths:
        echo("No files found matching the specified patterns", err=True)
        sys.exit(ExitCode.NO_FILES_FOUND)

    # If dry-run, show which files would be sent and exit
    # IMPORTANT: Do this after all of the include/exclude and filtering logic
    if dry_run:
        echo("\n[DRY RUN] Files that would be checked:")
        echo("=" * 50)

        # Get relative paths for display
        display_paths = []
        for file_path in file_paths:
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                # If not relative to cwd, try relative to git root
                try:
                    repo = git.Repo(search_parent_directories=True)
                    rel_path = file_path.relative_to(repo.working_dir)
                except (git.InvalidGitRepositoryError, git.NoSuchPathError):
                    # Not in a git repo or path doesn't exist - use absolute path
                    rel_path = file_path
                except (AttributeError, TypeError):
                    # Git repo issues - use absolute path
                    rel_path = file_path
            display_paths.append(str(rel_path))

        # Sort paths for consistent output
        display_paths.sort()

        # Show up to 50 files
        max_display = 50
        for i, path in enumerate(display_paths[:max_display], 1):
            echo(f"  {i:3d}. {path}")

        # If more than 50 files, show count
        if len(display_paths) > max_display:
            remaining = len(display_paths) - max_display
            echo(f"  ...and {remaining} more")

        echo("=" * 50)
        echo(f"Total files: {len(file_paths)}")
        echo("\nNote: This is a dry run. No files were actually sent for checking.")
        sys.exit(ExitCode.SUCCESS)

    # Read file contents
    files = []
    for file_path in file_paths:
        try:
            content = file_path.read_text()
            files.append({"path": str(file_path), "content": content})
        except (OSError, IOError, UnicodeDecodeError) as e:
            echo(
                f"Error reading {file_path}: {e}",
                persona=Persona.POWER_USER,
                err=True,
            )
            continue

    if not files:
        echo("No files could be read", err=True)
        sys.exit(ExitCode.FILE_READ_ERROR)

    async def check_files():
        # Store relative paths for use in batch processing
        get_relative_paths(file_paths, base_path)

        # Build file metadata for LOC tracking
        file_metadata = {}
        for file_dict in files:
            file_path = file_dict["path"]
            content = file_dict["content"]
            file_metadata[file_path] = {
                "loc": len(content.splitlines()),
            }

        try:
            async with ZenableMCPClient() as client:
                # Process files in batches, showing progress
                results = await client.check_conformance(
                    files, batch_size=5, show_progress=True, ctx=ctx
                )

                # Parse results into structured data models with file metadata
                report = parse_conformance_results(results, file_metadata=file_metadata)

                # Display formatted output
                show_conformance_summary(report)

                # Track usage before exit
                record_command_usage(
                    ctx=ctx,
                    loc=report.total_loc,
                    finding_suggestion=report.total_findings,
                    passed_checks=report.passed_checks,
                    failed_checks=report.failed_checks,
                    warning_checks=report.warning_checks,
                    total_checks_run=report.total_checks_run,
                    total_files_checked=report.total_files_checked,
                )

                # Exit with appropriate code based on findings
                if report.has_findings:
                    sys.exit(ExitCode.CONFORMANCE_ISSUES_FOUND)

        except (APIError, ConfigurationError) as e:
            echo(f"Error: {e}", err=True)
            # Track usage for error case
            record_command_usage(ctx=ctx, error=e)
            sys.exit(ExitCode.API_ERROR)
        except KeyboardInterrupt:
            echo("\nOperation cancelled by user.", err=True)
            sys.exit(ExitCode.USER_INTERRUPT)
        except Exception as e:
            # Catch any other unexpected errors from the MCP client
            echo(f"Error: {e}", err=True)
            # Track usage for error case
            record_command_usage(ctx=ctx, error=e)
            sys.exit(ExitCode.API_ERROR)

    asyncio.run(check_files())
