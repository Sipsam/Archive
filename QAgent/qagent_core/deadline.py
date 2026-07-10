"""Monotonic execution deadline shared by Agent, API, and Tool calls."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionDeadline:
    """An absolute monotonic deadline that cannot be extended by child calls."""

    expires_at: float

    @classmethod
    def from_start(
        cls, started_at: float, timeout_seconds: float
    ) -> "ExecutionDeadline":
        """Create a deadline from a monotonic start time and timeout seconds."""
        return cls(float(started_at) + max(float(timeout_seconds), 0.0))

    def remaining_seconds(self) -> float:
        """Return the non-negative number of seconds before expiry."""
        return max(self.expires_at - time.monotonic(), 0.0)

    def remaining_ms(self) -> float:
        """Return remaining time in milliseconds for trace metadata."""
        return round(self.remaining_seconds() * 1000, 2)

    def expired(self) -> bool:
        """Return whether the deadline has already elapsed."""
        return self.remaining_seconds() <= 0.0

    def bounded_timeout(self, requested_seconds: float) -> float:
        """Return a timeout no longer than either the request or global deadline."""
        return min(max(float(requested_seconds), 0.0), self.remaining_seconds())
