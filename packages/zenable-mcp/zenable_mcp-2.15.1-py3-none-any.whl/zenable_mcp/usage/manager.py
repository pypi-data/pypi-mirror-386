"""Usage data management for zenable_mcp commands."""

import json
import os
from datetime import datetime, timezone
from http.client import HTTPException

import click
import requests

from zenable_mcp import __version__
from zenable_mcp.constants import OAUTH_TOKEN_CACHE_DIR
from zenable_mcp.logging.logged_echo import echo
from zenable_mcp.logging.persona import Persona
from zenable_mcp.usage.fingerprint import get_system_fingerprint
from zenable_mcp.usage.models import (
    IDEOperationResult,
    ZenableMcpUsagePayload,
)
from zenable_mcp.usage.sender import send_usage_data
from zenable_mcp.utils.install_status import InstallResult

# Base Zenable URL (override with ZENABLE_URL env var)
_zenable_url = os.environ.get("ZENABLE_URL", "https://www.zenable.app").rstrip("/")

# Private usage API endpoint
_usage_api = f"{_zenable_url}/api/data/usage"

# Timeout for authenticated usage requests (in seconds)
AUTH_REQUEST_TIMEOUT = 5


def is_usage_enabled() -> bool:
    """
    Check if usage data collection is enabled.

    Returns:
        True if usage data collection is enabled, False if disabled via environment variable
    """
    return os.environ.get("ZENABLE_DISABLE_USAGE_TRACKING", "").lower() not in (
        "1",
        "true",
        "yes",
    )


def get_jwt_token_from_cache() -> str | None:
    """
    Extract JWT token from OAuth cache if available.

    Returns:
        JWT token string if available, None otherwise
    """
    try:
        # Check OAuth cache directory
        if not OAUTH_TOKEN_CACHE_DIR.exists():
            return None

        # Look for token file (FastMCP naming convention)
        # FastMCP stores tokens in files like "mcp_zenable_app.json"
        token_files = list(OAUTH_TOKEN_CACHE_DIR.glob("*.json"))

        for token_file in token_files:
            try:
                with open(token_file, encoding="utf-8") as f:
                    token_data = json.load(f)
                    # FastMCP stores tokens in nested structure: data.token_payload.access_token
                    if "data" in token_data and "token_payload" in token_data["data"]:
                        payload = token_data["data"]["token_payload"]
                        token = payload.get("access_token") or payload.get("id_token")
                        if token:
                            return token
                    # Fallback to top-level keys for compatibility
                    token = token_data.get("access_token") or token_data.get("id_token")
                    if token:
                        return token
            except Exception:
                continue

        return None

    except Exception:
        return None


def send_authenticated_usage(
    command_name: str,  # "check" or "hook"
    usage_data: dict,
    jwt_token: str | None,
) -> None:
    """
    Send usage data to authenticated data_api endpoint.

    Args:
        command_name: Command name ("check" or "hook")
        usage_data: Usage data dictionary
        jwt_token: JWT token from OAuth flow (if available)
    """
    if not jwt_token:
        return

    try:
        # Determine integration identifier
        integration = f"zenable_mcp/{command_name}"

        # Build request body
        request_body = {
            "integration": integration,
            "usage_data": usage_data,
        }

        # Send with JWT authentication
        requests.post(
            _usage_api,
            json=request_body,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
            },
            timeout=AUTH_REQUEST_TIMEOUT,
        )

    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        HTTPException,
        json.JSONDecodeError,
        Exception,
    ):
        pass


def extract_command_info(ctx: click.Context) -> tuple[str, dict[str, object]]:
    """
    Extract command name and arguments from click context.

    Args:
        ctx: Click context from command execution

    Returns:
        Tuple of (command_string, command_args_dict)
    """
    # Build command string from context
    command_parts = []
    current_ctx = ctx

    # Walk up the context chain to build full command
    while current_ctx:
        if current_ctx.info_name:
            command_parts.insert(0, current_ctx.info_name)
        current_ctx = current_ctx.parent

    command_string = " ".join(command_parts)

    # Extract command arguments (params)
    command_args = {}
    if ctx.params:
        # Filter out None values and convert to serializable types
        for key, value in ctx.params.items():
            if value is not None:
                # Convert tuples to lists for JSON serialization
                if isinstance(value, tuple):
                    command_args[key] = list(value)
                else:
                    command_args[key] = value

    return command_string, command_args


def convert_install_results_to_operations(
    results: list[InstallResult],
) -> list[IDEOperationResult]:
    """
    Convert InstallResult objects to IDEOperationResult for usage data.

    Args:
        results: List of InstallResult objects

    Returns:
        List of IDEOperationResult objects
    """
    operations = []

    for result in results:
        # Extract IDE name from component_name (e.g., "Cursor" -> "cursor")
        ide_name = result.component_name.lower()

        # Determine operation type from status
        operation = "install"  # default
        if result.status.value == "upgraded":
            operation = "upgrade"

        # Convert status to string
        status = result.status.value

        # Determine if global based on result attributes
        is_global = getattr(result, "is_global", False)

        operations.append(
            IDEOperationResult(
                ide_name=ide_name,
                operation=operation,
                status=status,
                is_global=is_global,
                message=result.message,
            )
        )

    return operations


def record_command_usage(
    ctx: click.Context,
    results: list[InstallResult] | None = None,
    error: Exception | None = None,
    **kwargs,
) -> None:
    """
    Record usage data for a zenable_mcp command.

    Sends usage data to both:
    1. Public API (unauthenticated, system fingerprint)
    2. Data API (authenticated, user-associated)

    Args:
        ctx: Click context from command execution
        results: Optional list of InstallResult objects from IDE operations
        error: Optional exception if command failed
        **kwargs: Additional data to include (e.g., loc, finding_suggestion)
    """
    # Check if usage data collection is disabled
    if not is_usage_enabled():
        return

    try:
        # Get system fingerprint
        system_info, system_hash = get_system_fingerprint()

        # Extract command info
        command_string, command_args = extract_command_info(ctx)

        # Determine command name (check or hook)
        command_name = ctx.info_name  # "check" or "hook"

        # Convert InstallResult objects to IDEOperationResult
        ide_operations = []
        if results:
            ide_operations = convert_install_results_to_operations(results)

        # Determine success status
        success = error is None
        if results:
            # If any result is an error, mark as not successful
            success = success and not any(r.is_error for r in results)

        # Build error message
        error_message = None
        if error:
            error_message = str(error)

        # Build usage data dictionary (for authenticated endpoint)
        usage_data = {
            "command": command_string,
            "command_args": command_args,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "error_message": error_message,
            "zenable_mcp_version": __version__,
        }

        # Add metrics (loc and finding_suggestion are always required)
        usage_data["loc"] = kwargs.get("loc", 0)
        usage_data["finding_suggestion"] = kwargs.get("finding_suggestion", 0)

        # Add all other int metrics if provided
        for metric in [
            "passed_checks",
            "failed_checks",
            "warning_checks",
            "total_checks_run",
            "total_files_checked",
        ]:
            if metric in kwargs:
                usage_data[metric] = kwargs[metric]

        # Get JWT token to determine which endpoints to use
        jwt_token = get_jwt_token_from_cache()

        # For check/hook commands with authentication, ONLY use authenticated endpoint
        # For all other commands or when not authenticated, use public endpoint
        should_skip_public = jwt_token and command_name in ["check", "hook"]

        # 1. Send to public API (unless we're authenticated check/hook)
        if not should_skip_public:
            payload = ZenableMcpUsagePayload(
                system_info=system_info,
                system_hash=system_hash,
                command=command_string,
                command_args=command_args,
                timestamp=datetime.now(timezone.utc),
                ide_operations=ide_operations,
                success=success,
                error_message=error_message,
                zenable_mcp_version=__version__,
            )
            send_usage_data(payload)

        # 2. Send to authenticated data_api endpoint (for check/hook with token)
        if jwt_token and command_name in ["check", "hook"]:
            send_authenticated_usage(command_name, usage_data, jwt_token)

    except Exception as e:
        # Never fail the main command due to usage data errors
        echo(
            f"Failed to record usage data: {type(e).__name__}: {e}",
            err=True,
            persona=Persona.DEVELOPER,
        )
