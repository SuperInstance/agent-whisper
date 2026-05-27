"""InfluenceTracker — measure and track cumulative influence effects."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class InfluenceRecord:
    """A record of a single influence event."""
    source: str
    target: str
    influence_type: str  # "whisper", "nudge", "channel"
    influence_id: str
    strength: float
    timestamp: float = field(default_factory=time.time)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class InfluenceSummary:
    """Aggregated influence metrics for an agent."""
    agent_id: str
    total_inbound: float = 0.0
    total_outbound: float = 0.0
    influence_count: int = 0
    by_type: dict[str, float] = field(default_factory=dict)
    by_source: dict[str, float] = field(default_factory=dict)
    top_influencer: Optional[str] = None


class InfluenceTracker:
    """Track cumulative influence effects across agents.

    The InfluenceTracker records every influence event (whispers, nudges,
    channel messages) and provides aggregated metrics to understand who
    is influencing whom, and by how much.

    Example::

        tracker = InfluenceTracker()
        tracker.record("alice", "bob", "whisper", "w-123", strength=0.7)
        tracker.record("carol", "bob", "nudge", "n-456", strength=0.4)

        summary = tracker.summary("bob")
        print(summary.total_inbound)   # 1.1
        print(summary.top_influencer)  # "alice"
    """

    def __init__(self, max_records: int = 10_000) -> None:
        self.max_records = max_records
        self._records: list[InfluenceRecord] = []

    def record(
        self,
        source: str,
        target: str,
        influence_type: str,
        influence_id: str,
        strength: float = 0.5,
        context: Optional[dict[str, Any]] = None,
    ) -> InfluenceRecord:
        """Record an influence event.

        Args:
            source: Agent exerting influence.
            target: Agent receiving influence.
            influence_type: Category ("whisper", "nudge", "channel").
            influence_id: Unique ID of the influence artifact.
            strength: Effective strength (0.0–1.0).
            context: Optional additional context.

        Returns:
            The created InfluenceRecord.

        Raises:
            ValueError: If strength is out of range.
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be 0.0–1.0, got {strength}")

        rec = InfluenceRecord(
            source=source,
            target=target,
            influence_type=influence_type,
            influence_id=influence_id,
            strength=strength,
            context=context or {},
        )

        self._records.append(rec)

        # Evict oldest if over limit
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

        return rec

    def records_for(
        self,
        agent_id: str,
        direction: str = "inbound",
        since: Optional[float] = None,
    ) -> list[InfluenceRecord]:
        """Get influence records for an agent.

        Args:
            agent_id: The agent to query.
            direction: "inbound" (target=agent), "outbound" (source=agent), or "both".
            since: Only return records after this timestamp.

        Returns:
            Matching influence records.
        """
        result: list[InfluenceRecord] = []
        for rec in self._records:
            if since is not None and rec.timestamp < since:
                continue
            if direction == "inbound" and rec.target == agent_id:
                result.append(rec)
            elif direction == "outbound" and rec.source == agent_id:
                result.append(rec)
            elif direction == "both" and (rec.source == agent_id or rec.target == agent_id):
                result.append(rec)
        return result

    def summary(
        self,
        agent_id: str,
        since: Optional[float] = None,
    ) -> InfluenceSummary:
        """Compute aggregated influence metrics for an agent.

        Args:
            agent_id: Agent to summarize.
            since: Only consider records after this timestamp.

        Returns:
            InfluenceSummary with aggregated metrics.
        """
        inbound = self.records_for(agent_id, "inbound", since)
        outbound = self.records_for(agent_id, "outbound", since)

        by_type: dict[str, float] = {}
        by_source: dict[str, float] = {}
        total_in = 0.0

        for rec in inbound:
            total_in += rec.strength
            by_type[rec.influence_type] = by_type.get(rec.influence_type, 0.0) + rec.strength
            by_source[rec.source] = by_source.get(rec.source, 0.0) + rec.strength

        total_out = sum(r.strength for r in outbound)

        top_influencer = max(by_source, key=by_source.get) if by_source else None

        return InfluenceSummary(
            agent_id=agent_id,
            total_inbound=round(total_in, 4),
            total_outbound=round(total_out, 4),
            influence_count=len(inbound) + len(outbound),
            by_type=by_type,
            by_source=by_source,
            top_influencer=top_influencer,
        )

    def influence_between(
        self,
        source: str,
        target: str,
        since: Optional[float] = None,
    ) -> float:
        """Total influence from source to target.

        Returns:
            Sum of all influence strengths from source→target.
        """
        total = 0.0
        for rec in self._records:
            if rec.source == source and rec.target == target:
                if since is None or rec.timestamp >= since:
                    total += rec.strength
        return round(total, 4)

    def top_influencers(self, limit: int = 10) -> list[tuple[str, float]]:
        """Rank agents by total outbound influence.

        Returns:
            List of (agent_id, total_outbound_strength) sorted descending.
        """
        outbound: dict[str, float] = {}
        for rec in self._records:
            outbound[rec.source] = outbound.get(rec.source, 0.0) + rec.strength

        ranked = sorted(outbound.items(), key=lambda x: x[1], reverse=True)
        return ranked[:limit]

    def clear(self) -> None:
        """Clear all records."""
        self._records.clear()

    def record_count(self) -> int:
        """Total number of records."""
        return len(self._records)
