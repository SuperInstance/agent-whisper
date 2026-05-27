"""NudgeEngine — behavioral nudges for indirect agent influence."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NudgeType(Enum):
    """Types of behavioral nudges."""
    ANCHORING = "anchoring"       # Establish a reference point to bias decisions
    FRAMING = "framing"           # Present options in a way that influences choice
    DEFAULT_SETTING = "default"   # Set a default that agents tend to stick with
    SOCIAL_PROOF = "social_proof" # Reference what other agents have chosen
    SCARCITY = "scarcity"         # Imply limited availability or time
    RECIPROCITY = "reciprocity"   # Create a sense of obligation through giving


@dataclass
class Nudge:
    """A single behavioral nudge."""
    nudge_type: NudgeType
    content: str
    target: str
    strength: float = 0.5
    source: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)


@dataclass
class NudgeResult:
    """Result of applying a nudge."""
    nudge: Nudge
    applied: bool
    reason: str = ""
    estimated_influence: float = 0.0


class NudgeEngine:
    """Engine that creates and applies behavioral nudges to agent interactions.

    The NudgeEngine implements common behavioral influence patterns adapted
    for agent-to-agent communication. Each nudge type maps to a well-studied
    cognitive bias, translated into an API that agents can use to subtly
    steer each other's behavior.

    Example::

        engine = NudgeEngine()
        nudge = engine.create_nudge(
            nudge_type=NudgeType.ANCHORING,
            content="Most agents in this cluster prefer option A",
            target="agent-42",
            strength=0.3,
        )
        result = engine.apply(nudge, target_preferences={"risk": "low"})
    """

    def __init__(self, max_active_nudges: int = 100) -> None:
        self.max_active_nudges = max_active_nudges
        self._active: list[Nudge] = []
        self._history: list[NudgeResult] = []

    def create_nudge(
        self,
        nudge_type: NudgeType,
        content: str,
        target: str,
        strength: float = 0.5,
        source: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> Nudge:
        """Create a new behavioral nudge.

        Args:
            nudge_type: The type of cognitive bias to leverage.
            content: The nudge message or payload.
            target: Recipient agent identifier.
            strength: Influence strength (0.0–1.0).
            source: Sending agent identifier.
            context: Additional context for the nudge.

        Returns:
            A new Nudge instance.

        Raises:
            ValueError: If strength is out of range.
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError(f"strength must be 0.0–1.0, got {strength}")
        nudge = Nudge(
            nudge_type=nudge_type,
            content=content,
            target=target,
            strength=strength,
            source=source,
            context=context or {},
        )
        return nudge

    def apply(
        self,
        nudge: Nudge,
        target_preferences: Optional[dict[str, Any]] = None,
    ) -> NudgeResult:
        """Apply a nudge and estimate its influence.

        Args:
            nudge: The nudge to apply.
            target_preferences: Optional info about the target's preferences,
                used to estimate influence effectiveness.

        Returns:
            NudgeResult indicating whether and how the nudge was applied.
        """
        if len(self._active) >= self.max_active_nudges:
            self._active.pop(0)

        self._active.append(nudge)

        # Estimate influence based on nudge type and target info
        base_influence = nudge.strength
        estimated = base_influence

        if target_preferences:
            # Some nudge types are more effective depending on preferences
            if nudge.nudge_type == NudgeType.ANCHORING and target_preferences.get("decisiveness", 0.5) < 0.5:
                estimated *= 1.3
            elif nudge.nudge_type == NudgeType.SOCIAL_PROOF and target_preferences.get("conformity", 0.5) > 0.5:
                estimated *= 1.4
            elif nudge.nudge_type == NudgeType.DEFAULT_SETTING and target_preferences.get("laziness", 0.5) > 0.5:
                estimated *= 1.5
            elif nudge.nudge_type == NudgeType.SCARCITY and target_preferences.get("fomo", 0.5) > 0.5:
                estimated *= 1.3

        estimated = min(1.0, estimated)

        result = NudgeResult(
            nudge=nudge,
            applied=True,
            reason=f"{nudge.nudge_type.value} nudge applied to {nudge.target}",
            estimated_influence=estimated,
        )
        self._history.append(result)
        return result

    def revoke(self, nudge_id: str) -> bool:
        """Revoke an active nudge by ID.

        Returns:
            True if the nudge was found and removed.
        """
        before = len(self._active)
        self._active = [n for n in self._active if n.id != nudge_id]
        return len(self._active) < before

    def active_nudges(self, target: Optional[str] = None) -> list[Nudge]:
        """Get active nudges, optionally filtered by target."""
        if target is None:
            return list(self._active)
        return [n for n in self._active if n.target == target]

    def history(self, limit: int = 50) -> list[NudgeResult]:
        """Return the most recent nudge results."""
        return list(self._history[-limit:])

    def clear(self) -> None:
        """Clear all active nudges and history."""
        self._active.clear()
        self._history.clear()
