"""Retry/backoff utilities.

Backoff schedule (default): 200 → 400 → 800 → 1600 ms (cap)
Attempts: 3 by default (inclusive — i.e., up to 3 calls)
Overall timeout guard to 5s configurable via parameter.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar, Iterable, Tuple

T = TypeVar("T")


def exponential_backoff(
    attempt: int, base_delay: float = 0.2, factor: float = 2.0, max_delay: float = 1.6
) -> float:
    """Compute exponential backoff delay in seconds for a given attempt index.

    attempt: Zero-based attempt index (0 for first retry wait)
    base_delay: Starting delay in seconds (default 0.2s)
    factor: Multiplier per attempt (default 2.0)
    max_delay: Maximum delay in seconds (default 1.6s)
    """
    delay = base_delay * (factor**attempt)
    if delay > max_delay:
        return max_delay
    return delay


def default_backoff_ms() -> Iterable[int]:
    """Default backoff sequence in milliseconds for up to 4 waits."""
    # Map the first 4 exponential backoff delays to milliseconds
    return [int(exponential_backoff(i) * 1000) for i in range(4)]


def retry(
    fn: Callable[[], T], attempts: int = 3, timeout_s: float = 5.0
) -> Tuple[bool, T | Exception]:
    """Retry a callable up to `attempts` times within `timeout_s` seconds.

    Returns a tuple (success, result_or_exception). If the overall elapsed time
    exceeds `timeout_s`, the function returns (False, TimeoutError(...)), even if
    an attempt succeeds after the timeout budget is exceeded. This behavior
    matches the expectations in unit tests that a too-short timeout should fail.
    """
    start = time.monotonic()
    last_exc: Exception | None = None
    backoffs_ms = list(default_backoff_ms())

    for i in range(attempts):
        # Pre-attempt timeout guard
        if time.monotonic() - start > timeout_s:
            break

        try:
            result = fn()
            # Post-attempt timeout guard — treat as timeout if we exceeded the budget
            if time.monotonic() - start > timeout_s:
                return False, TimeoutError("Retry operation exceeded timeout")
            return True, result
        except Exception as e:  # noqa: BLE001
            last_exc = e

        # If that was the last allowed attempt, stop
        if i == attempts - 1:
            break

        # Timeout guard before sleeping
        if time.monotonic() - start > timeout_s:
            break

        # Sleep with exponential backoff (cap at the last defined delay)
        delay_ms = backoffs_ms[i] if i < len(backoffs_ms) else backoffs_ms[-1]
        time.sleep(delay_ms / 1000.0)

    # If we broke due to timeout and never had an exception, surface a TimeoutError
    if last_exc is None:
        last_exc = TimeoutError("Retry operation exceeded timeout")
    return False, last_exc
