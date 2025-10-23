"""Retry utilities for handling transient errors."""

import asyncio
import functools
import inspect
import random
import time
import warnings
from typing import Any, Callable, Optional, TypeVar

import httpx
import requests

T = TypeVar("T")


def is_transient_error(e: Exception, rate_limit_only: bool = False) -> bool:
    """
    Check if an exception is likely transient and worth retrying.

    Args:
        e: The exception to check
        rate_limit_only: If True, only check for rate limit errors

    Includes:
    - Rate limits (429, 403 with "rate limit")
    - Server errors (5xx) - unless rate_limit_only is True
    - Connection errors - unless rate_limit_only is True
    - Timeouts - unless rate_limit_only is True
    - httpx protocol errors - unless rate_limit_only is True
    """
    # Check for httpx HTTPStatusError with rate limit status codes
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 429 or (
            e.response.status_code == 403 and "rate limit" in str(e).lower()
        ):
            return True
        # Check for server errors (unless only checking rate limits)
        if not rate_limit_only and 500 <= e.response.status_code < 600:
            return True

    # Check for httpx protocol and network errors (unless only checking rate limits)
    if not rate_limit_only:
        if isinstance(
            e,
            (
                httpx.RemoteProtocolError,
                httpx.ReadError,
                httpx.WriteError,
                httpx.ConnectError,
                httpx.PoolTimeout,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.NetworkError,
            ),
        ):
            return True

    # Check for requests HTTPError
    if isinstance(e, requests.HTTPError) and hasattr(e, "response") and e.response:
        # Check for rate limits
        if e.response.status_code == 429 or (
            e.response.status_code == 403 and "rate limit" in str(e).lower()
        ):
            return True

        # Check for server errors (unless only checking rate limits)
        if not rate_limit_only and 500 <= e.response.status_code < 600:
            return True

        # If it's an HTTPError with a response but not a transient status, return False
        return False

    # Check for rate limiting failures or server errors, such as those from GitHub-specific exceptions (e.g., from PyGithub)
    # We check by attribute rather than importing to avoid the dependency
    if hasattr(e, "status"):
        status = getattr(e, "status", None)
        if status == 429 or (status == 403 and "rate limit" in str(e).lower()):
            return True

        # Check for server errors
        if not rate_limit_only and status and 500 <= status < 600:
            return True

    # Check for connection/network errors (unless only checking rate limits)
    # Note: we exclude requests.HTTPError here because it's handled above
    if (
        not rate_limit_only
        and isinstance(
            e,
            (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ChunkedEncodingError,
                TimeoutError,
                OSError,
            ),
        )
        and not isinstance(e, requests.HTTPError)
    ):
        return True

    return False


def _setup_retry_parameters(
    rate_limit_only: bool,
    exceptions: Optional[tuple[type[Exception], ...]],
    retryable_conditions: Optional[Callable[[Exception], bool]],
    warning_message_func: Optional[Callable[[Exception, int, int, float], str]],
) -> tuple[
    tuple[type[Exception], ...],
    Optional[Callable[[Exception], bool]],
    Optional[Callable[[Exception, int, int, float], str]],
]:
    """
    Set up retry parameters with defaults based on rate_limit_only.

    Args:
        rate_limit_only: If True, only retry on rate limit errors
        exceptions: Tuple of exception types to catch
        retryable_conditions: Function to determine if error should be retried
        warning_message_func: Function to generate warning messages

    Returns:
        Tuple of (exceptions, retryable_conditions, warning_message_func)
    """
    # Set default exceptions
    if exceptions is None:
        exceptions = (
            (requests.exceptions.HTTPError,) if rate_limit_only else (Exception,)
        )

    # Set up default conditions based on rate_limit_only
    if retryable_conditions is None and rate_limit_only:

        def _default_rate_limit_condition(e: Exception) -> bool:
            return is_transient_error(e, rate_limit_only=True)

        retryable_conditions = _default_rate_limit_condition

    # Set up default warning message for rate limits
    if warning_message_func is None and rate_limit_only:

        def _default_rate_limit_warning(
            e: Exception, attempt: int, max_retries: int, delay: float
        ) -> str:
            return f"Rate limit hit, retrying in {delay:.1f} seconds (attempt {attempt + 1}/{max_retries})"

        warning_message_func = _default_rate_limit_warning

    return exceptions, retryable_conditions, warning_message_func


def retry_on_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: Optional[tuple[type[Exception], ...]] = None,
    retryable_conditions: Optional[Callable[[Exception], bool]] = None,
    warning_message_func: Optional[Callable[[Exception, int, int, float], str]] = None,
    rate_limit_only: bool = False,
    excluded_exceptions: Optional[tuple[type[Exception], ...]] = None,
):
    """
    Decorator to retry a function on specified errors with exponential backoff.

    Automatically handles both sync and async functions.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to multiply the delay by for each retry
        exceptions: Tuple of exception types to catch and potentially retry on
        retryable_conditions: Optional function that takes an exception and returns
                            True if the error should be retried
        warning_message_func: Optional function to generate custom warning messages.
                            Takes (exception, attempt, max_retries, delay) and returns str.
        rate_limit_only: If True, only retry on rate limit errors (429, 403 with "rate limit")
        excluded_exceptions: Optional tuple of exception types to exclude from retrying
    """
    exceptions, retryable_conditions, warning_message_func = _setup_retry_parameters(
        rate_limit_only, exceptions, retryable_conditions, warning_message_func
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                delay = initial_delay
                last_exception = None

                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        # Check if the exception should be excluded
                        if excluded_exceptions and isinstance(exc, excluded_exceptions):
                            raise
                        last_exception = exc

                        # Check if we should retry this error
                        should_retry = True
                        if retryable_conditions:
                            should_retry = retryable_conditions(exc)

                        if not should_retry:
                            raise

                        if attempt == max_retries:
                            # No more retries left
                            raise

                        # Calculate next delay with exponential backoff and jitter
                        base_delay = min(delay, max_delay)
                        # Add jitter: ±20% of base delay
                        jittered_delay = round(
                            random.uniform(0.8 * base_delay, 1.2 * base_delay), 2
                        )

                        # Generate warning message
                        if warning_message_func:
                            warning_msg = warning_message_func(
                                exc, attempt, max_retries, jittered_delay
                            )
                        else:
                            warning_msg = (
                                f"{type(exc).__name__} occurred, retrying in {jittered_delay:.1f} seconds "
                                f"(attempt {attempt + 1}/{max_retries}): {str(exc)}"
                            )

                        warnings.warn(warning_msg, UserWarning, stacklevel=2)

                        await asyncio.sleep(jittered_delay)
                        delay *= backoff_factor
                        continue

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                delay = initial_delay
                last_exception = None

                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as exc:
                        # Check if the exception should be excluded
                        if excluded_exceptions and isinstance(exc, excluded_exceptions):
                            raise
                        last_exception = exc

                        # Check if we should retry this error
                        should_retry = True
                        if retryable_conditions:
                            should_retry = retryable_conditions(exc)

                        if not should_retry:
                            raise

                        if attempt == max_retries:
                            # No more retries left
                            raise

                        # Calculate next delay with exponential backoff and jitter
                        base_delay = min(delay, max_delay)
                        # Add jitter: ±20% of base delay
                        jittered_delay = round(
                            random.uniform(0.8 * base_delay, 1.2 * base_delay), 2
                        )

                        # Generate warning message
                        if warning_message_func:
                            warning_msg = warning_message_func(
                                exc, attempt, max_retries, jittered_delay
                            )
                        else:
                            warning_msg = (
                                f"{type(exc).__name__} occurred, retrying in {jittered_delay:.1f} seconds "
                                f"(attempt {attempt + 1}/{max_retries}): {str(exc)}"
                            )

                        warnings.warn(warning_msg, UserWarning, stacklevel=2)

                        time.sleep(jittered_delay)
                        delay *= backoff_factor
                        continue

                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception

            return sync_wrapper

    return decorator
