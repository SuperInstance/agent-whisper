"""Whisper — the fundamental unit of subtle agent influence."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class WhisperState(Enum):
    """Lifecycle state of a whisper."""
    PENDING = "pending"
    ACTIVE = "active"
    FADING = "fading"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class Whisper:
    """A whisper is a subtle signal sent between agents.

    Unlike direct messages, whispers carry content with configurable
    intensity that decays over time — like a fading scent or a distant
    echo. They're designed for indirect influence rather than explicit
    commands.

    Attributes:
        content: The payload of the whisper — text, data, or signal.
        intensity: Strength from 0.0 (barely perceptible) to 1.0 (unmistakable).
        target: Recipient agent identifier (or "*" for broadcast).
        duration: How long (seconds) the whisper remains at full intensity.
        decay_rate: How fast intensity drops after duration expires (0.0–1.0).
        source: Sender agent identifier.
        metadata: Arbitrary key-value pairs for context.
    """

    content: str
    intensity: float = 0.5
    target: str = "*"
    duration: float = 60.0
    decay_rate: float = 0.1
    source: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    state: WhisperState = WhisperState.PENDING

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"intensity must be 0.0–1.0, got {self.intensity}")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError(f"decay_rate must be 0.0–1.0, got {self.decay_rate}")
        if self.duration < 0:
            raise ValueError(f"duration must be non-negative, got {self.duration}")

    def activate(self) -> None:
        """Transition the whisper to active state."""
        if self.state == WhisperState.PENDING:
            self.state = WhisperState.ACTIVE

    def revoke(self) -> None:
        """Immediately revoke the whisper."""
        self.state = WhisperState.REVOKED

    def current_intensity(self, now: Optional[float] = None) -> float:
        """Calculate current effective intensity after decay.

        Args:
            now: Current timestamp. Defaults to time.time().

        Returns:
            Effective intensity (0.0–1.0).
        """
        if self.state == WhisperState.REVOKED:
            return 0.0
        if self.state == WhisperState.PENDING:
            return 0.0

        now = now if now is not None else time.time()
        elapsed = now - self.created_at

        if elapsed <= self.duration:
            return self.intensity

        # Exponential decay after duration expires
        over = elapsed - self.duration
        decayed = self.intensity * (1.0 - self.decay_rate) ** (over / self.duration)
        return max(0.0, decayed)

    def tick(self, now: Optional[float] = None) -> WhisperState:
        """Update state based on current time.

        Returns:
            Updated state.
        """
        if self.state in (WhisperState.REVOKED, WhisperState.PENDING):
            return self.state

        effective = self.current_intensity(now)
        if effective <= 0.001:
            self.state = WhisperState.EXPIRED
        elif effective < self.intensity * 0.5:
            self.state = WhisperState.FADING
        else:
            self.state = WhisperState.ACTIVE
        return self.state

    def is_expired(self, now: Optional[float] = None) -> bool:
        """Check if the whisper has fully decayed."""
        return self.tick(now) == WhisperState.EXPIRED

    def matches(self, agent_id: str) -> bool:
        """Check if this whisper targets a given agent."""
        return self.target == "*" or self.target == agent_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "intensity": self.intensity,
            "target": self.target,
            "source": self.source,
            "duration": self.duration,
            "decay_rate": self.decay_rate,
            "created_at": self.created_at,
            "state": self.state.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Whisper:
        """Deserialize from a plain dictionary."""
        data = dict(data)
        data["state"] = WhisperState(data.pop("state", "pending"))
        return cls(**data)
