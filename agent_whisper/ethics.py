"""EthicsGuard — transparency, consent, and limits for agent influence."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ConsentStatus(Enum):
    """Consent states."""
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class ConsentRecord:
    """Records an agent's consent to receive influence."""
    source: str
    target: str
    status: ConsentStatus = ConsentStatus.GRANTED
    granted_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    scope: list[str] = field(default_factory=lambda: ["whisper", "nudge", "channel"])
    id: str = field(default_factory=lambda: str(uuid.uuid4))

    def is_valid(self, now: Optional[float] = None) -> bool:
        """Check if consent is currently valid."""
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at is not None:
            now = now if now is not None else time.time()
            if now > self.expires_at:
                self.status = ConsentStatus.EXPIRED
                return False
        return True

    def allows(self, influence_type: str) -> bool:
        """Check if this consent covers a specific influence type."""
        return self.is_valid() and influence_type in self.scope


@dataclass
class InfluenceLimit:
    """Configurable limits on influence."""
    max_influence_per_source: float = 1.0   # Max cumulative from one source
    max_total_influence: float = 5.0         # Max total inbound
    max_nudges_per_hour: int = 20            # Rate limit on nudges
    require_consent: bool = True             # Whether consent is mandatory
    transparency_level: str = "full"         # "none", "summary", "full"


class EthicsViolation(Exception):
    """Raised when an influence action violates ethical constraints."""
    pass


class EthicsGuard:
    """Enforces transparency, consent, and limits on agent influence.

    The EthicsGuard acts as a gatekeeper for all influence operations.
    It tracks consent, enforces rate limits, and ensures that influence
    stays within configurable bounds.

    Example::

        guard = EthicsGuard()
        guard.grant_consent("alice", "bob", scope=["whisper"])
        guard.check("alice", "bob", "whisper", strength=0.5)  # OK
        guard.check("alice", "bob", "nudge", strength=0.3)    # raises EthicsViolation
    """

    def __init__(
        self,
        limits: Optional[InfluenceLimit] = None,
        default_consent: bool = False,
    ) -> None:
        self.limits = limits or InfluenceLimit()
        self.default_consent = default_consent
        self._consents: dict[str, list[ConsentRecord]] = {}
        self._influence_log: list[dict[str, Any]] = []
        self._nudge_timestamps: dict[str, list[float]] = {}

    def grant_consent(
        self,
        source: str,
        target: str,
        scope: Optional[list[str]] = None,
        ttl: Optional[float] = None,
    ) -> ConsentRecord:
        """Grant consent from target to source for influence.

        Args:
            source: The influencing agent.
            target: The agent granting consent.
            scope: Types of influence allowed (default: all).
            ttl: Time-to-live in seconds.

        Returns:
            The new ConsentRecord.
        """
        record = ConsentRecord(
            source=source,
            target=target,
            status=ConsentStatus.GRANTED,
            scope=scope or ["whisper", "nudge", "channel"],
            expires_at=(time.time() + ttl) if ttl else None,
        )
        key = f"{source}:{target}"
        if key not in self._consents:
            self._consents[key] = []
        self._consents[key].append(record)
        return record

    def revoke_consent(self, source: str, target: str) -> int:
        """Revoke all consent from target to source.

        Returns:
            Number of consent records revoked.
        """
        key = f"{source}:{target}"
        count = 0
        for rec in self._consents.get(key, []):
            if rec.status == ConsentStatus.GRANTED:
                rec.status = ConsentStatus.REVOKED
                count += 1
        return count

    def has_consent(
        self,
        source: str,
        target: str,
        influence_type: str = "whisper",
    ) -> bool:
        """Check if valid consent exists.

        Args:
            source: The influencing agent.
            target: The target agent.
            influence_type: The type of influence to check.

        Returns:
            True if consent exists and is valid.
        """
        if not self.limits.require_consent:
            return True

        if self.default_consent:
            return True

        key = f"{source}:{target}"
        for rec in self._consents.get(key, []):
            if rec.allows(influence_type):
                return True
        return False

    def check(
        self,
        source: str,
        target: str,
        influence_type: str,
        strength: float = 0.5,
        cumulative_from_source: float = 0.0,
        cumulative_total: float = 0.0,
    ) -> bool:
        """Check if an influence action is ethically permissible.

        Args:
            source: The influencing agent.
            target: The target agent.
            influence_type: Type of influence ("whisper", "nudge", "channel").
            strength: The strength of this influence.
            cumulative_from_source: Total influence already from this source.
            cumulative_total: Total influence already on this target.

        Returns:
            True if the action is allowed.

        Raises:
            EthicsViolation: If the action violates any constraint.
        """
        # Consent check
        if self.limits.require_consent and not self.has_consent(source, target, influence_type):
            raise EthicsViolation(
                f"No consent from {target} for {source} to send {influence_type}"
            )

        # Strength check
        if strength < 0.0 or strength > 1.0:
            raise EthicsViolation(f"Invalid strength: {strength}")

        # Cumulative limit from single source
        if (cumulative_from_source + strength) > self.limits.max_influence_per_source:
            raise EthicsViolation(
                f"Cumulative influence from {source} to {target} would exceed limit "
                f"({cumulative_from_source + strength:.2f} > {self.limits.max_influence_per_source})"
            )

        # Total limit
        if (cumulative_total + strength) > self.limits.max_total_influence:
            raise EthicsViolation(
                f"Total influence on {target} would exceed limit "
                f"({cumulative_total + strength:.2f} > {self.limits.max_total_influence})"
            )

        # Rate limit for nudges
        if influence_type == "nudge":
            now = time.time()
            key = f"{source}:{target}"
            stamps = self._nudge_timestamps.get(key, [])
            stamps = [t for t in stamps if now - t < 3600]
            if len(stamps) >= self.limits.max_nudges_per_hour:
                raise EthicsViolation(
                    f"Rate limit: {source} has sent {len(stamps)} nudges to {target} in the last hour"
                )
            stamps.append(now)
            self._nudge_timestamps[key] = stamps

        # Log the check
        self._influence_log.append({
            "source": source,
            "target": target,
            "type": influence_type,
            "strength": strength,
            "timestamp": time.time(),
            "allowed": True,
        })

        return True

    def audit(self, agent_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Get the influence audit log.

        Args:
            agent_id: If provided, filter to records involving this agent.

        Returns:
            List of audit log entries.
        """
        if agent_id is None:
            return list(self._influence_log)
        return [
            entry for entry in self._influence_log
            if entry["source"] == agent_id or entry["target"] == agent_id
        ]

    def transparency_report(self, target: str) -> dict[str, Any]:
        """Generate a transparency report for an agent.

        Shows all influence attempts targeting this agent, respecting
        the configured transparency_level.

        Returns:
            A dict summarizing influence received.
        """
        level = self.limits.transparency_level
        entries = [e for e in self._influence_log if e["target"] == target]

        if level == "none":
            return {"agent": target, "total_events": len(entries), "details": "hidden"}

        if level == "summary":
            by_source: dict[str, int] = {}
            for e in entries:
                by_source[e["source"]] = by_source.get(e["source"], 0) + 1
            return {"agent": target, "total_events": len(entries), "by_source": by_source}

        # "full"
        return {"agent": target, "total_events": len(entries), "events": entries}

    def clear(self) -> None:
        """Clear all consent records and audit logs."""
        self._consents.clear()
        self._influence_log.clear()
        self._nudge_timestamps.clear()
