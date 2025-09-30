"""Version compatibility checks between broker and CLI.

Rule:
- Major must match exactly
- Minor difference allowed within ±1
- Patch ignored for compatibility

Returns (compatible: bool, message: str)
"""

from __future__ import annotations

import re  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from typing import Tuple  # noqa: E402


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @staticmethod
    def parse(s: str) -> "SemVer":
        """Parse a semantic version string, ignoring prerelease/build metadata.

        Examples:
        - "1.2.3" → (1, 2, 3)
        - "1.0.0-beta.1" → (1, 0, 0)
        - "2.1" → (2, 1, 0)
        - invalid strings default to 0.0.0
        """
        s = s or "0.0.0"
        # Strip prerelease (+ build) metadata
        core = re.split(r"[-+]", s, maxsplit=1)[0]
        m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", core)
        if not m:
            return SemVer(0, 0, 0)
        major = int(m.group(1)) if m.group(1) else 0
        minor = int(m.group(2)) if m.group(2) else 0
        patch = int(m.group(3)) if m.group(3) else 0
        return SemVer(major, minor, patch)


def check_compat(cli: str, broker: str) -> Tuple[bool, str | None]:
    # Be lenient with invalid versions
    semver_like = re.compile(r"^\d+(?:\.\d+){0,2}(?:[-+].*)?$")
    if not semver_like.match(cli or "") or not semver_like.match(broker or ""):
        return True, None

    c = SemVer.parse(cli)
    b = SemVer.parse(broker)

    if c.major != b.major:
        return False, f"Incompatible major versions: cli={c.major}, broker={b.major}"

    # Same minor → fully compatible; include a friendly message for patch-only diffs
    if c.minor == b.minor:
        return True, "Compatible"

    # Compute signed difference (broker - cli)
    diff = b.minor - c.minor
    if diff > 0:
        # Broker is ahead
        if diff == 1:
            return True, None
        if diff >= 2:
            return True, (
                "Compatible (restricted): minor version skew="
                f"{diff}; certain features may be disabled (cli={cli}, broker={broker})"
            )
    else:
        # CLI is ahead
        if diff == -1:
            return True, (
                "Compatible (restricted): minor version skew=1; certain features may be disabled"
                f" (cli={cli}, broker={broker})"
            )
        if diff <= -2:
            return False, f"Minor versions too far apart: cli={c.minor}, broker={b.minor}"

    # Fallback (should not be reached)
    return True, None


def is_restricted(cli: str, broker: str) -> bool:
    """Return True when compatibility is allowed but in restricted mode.

    Restricted cases:
    - Broker is ahead by >= 2 minor versions
    - CLI is ahead by exactly 1 minor version
    """
    semver_like = re.compile(r"^\d+(?:\.\d+){0,2}(?:[-+].*)?$")
    if not semver_like.match(cli or "") or not semver_like.match(broker or ""):
        return False
    c = SemVer.parse(cli)
    b = SemVer.parse(broker)
    if c.major != b.major:
        return False
    diff = b.minor - c.minor
    return (diff >= 2) or (diff == -1)
