"""Deterministic deny-by-default example. NOT a complete authorization system."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def evaluate(*, permission: str, grants: frozenset[str]) -> PolicyDecision:
    if not permission or permission not in grants:
        return PolicyDecision(allowed=False, reason="DENY_NO_EXPLICIT_GRANT")
    return PolicyDecision(allowed=True, reason="ALLOW_EXPLICIT_GRANT")
