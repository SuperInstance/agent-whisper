"""WhisperChannel — indirect agent-to-agent messaging channel."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .whisper import Whisper, WhisperState


@dataclass
class ChannelMessage:
    """A message in a whisper channel."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = ""
    sender: str = ""
    content: str = ""
    timestamp: float = field(default_factory=time.time)
    ephemeral: bool = False
    ttl: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_alive(self, now: Optional[float] = None) -> bool:
        """Check if the message hasn't expired."""
        if not self.ephemeral or self.ttl is None:
            return True
        now = now if now is not None else time.time()
        return (now - self.timestamp) < self.ttl

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "sender": self.sender,
            "content": self.content,
            "timestamp": self.timestamp,
            "ephemeral": self.ephemeral,
            "ttl": self.ttl,
            "metadata": self.metadata,
        }


@dataclass
class ChannelInfo:
    """Metadata about a channel."""
    name: str
    members: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    creator: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4))


class WhisperChannel:
    """An indirect communication channel between agents.

    Unlike direct messaging, WhisperChannel supports named channels
    where agents can post whispers that other subscribed agents receive.
    Messages can be ephemeral (auto-expire) or persistent.

    Example::

        ch = WhisperChannel("strategy")
        ch.subscribe("agent-alice")
        ch.subscribe("agent-bob")

        msg = ch.send("agent-alice", "Consider approach B for the next iteration")
        msgs = ch.inbox("agent-bob")  # Returns messages for bob
    """

    def __init__(self, name: str) -> None:
        self._info = ChannelInfo(name=name)
        self._messages: list[ChannelMessage] = []
        self._whispers: list[Whisper] = []

    @property
    def name(self) -> str:
        return self._info.name

    @property
    def members(self) -> list[str]:
        return list(self._info.members)

    @property
    def info(self) -> ChannelInfo:
        return self._info

    def subscribe(self, agent_id: str) -> None:
        """Add an agent to the channel."""
        if agent_id not in self._info.members:
            self._info.members.append(agent_id)

    def unsubscribe(self, agent_id: str) -> bool:
        """Remove an agent from the channel.

        Returns:
            True if the agent was a member.
        """
        if agent_id in self._info.members:
            self._info.members.remove(agent_id)
            return True
        return False

    def send(
        self,
        sender: str,
        content: str,
        ephemeral: bool = False,
        ttl: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ChannelMessage:
        """Send a message to the channel.

        Args:
            sender: Agent ID of the sender.
            content: Message content.
            ephemeral: If True, message auto-expires after ttl seconds.
            ttl: Time-to-live in seconds for ephemeral messages.
            metadata: Optional metadata dict.

        Returns:
            The created ChannelMessage.

        Raises:
            ValueError: If sender is not a channel member.
        """
        if sender not in self._info.members:
            raise ValueError(f"{sender} is not a member of channel '{self.name}'")

        msg = ChannelMessage(
            channel=self.name,
            sender=sender,
            content=content,
            ephemeral=ephemeral,
            ttl=ttl,
            metadata=metadata or {},
        )
        self._messages.append(msg)
        return msg

    def whisper(
        self,
        whisper: Whisper,
    ) -> ChannelMessage:
        """Send a Whisper object through the channel.

        The whisper's intensity and decay properties are preserved,
        and the message acts as a carrier for the whisper.

        Returns:
            A ChannelMessage wrapping the whisper.
        """
        self._whispers.append(whisper)
        return self.send(
            sender=whisper.source or "unknown",
            content=whisper.content,
            metadata={"whisper_id": whisper.id, "intensity": whisper.intensity},
        )

    def inbox(
        self,
        agent_id: str,
        since: Optional[float] = None,
        include_expired: bool = False,
    ) -> list[ChannelMessage]:
        """Get messages visible to an agent.

        Args:
            agent_id: The requesting agent.
            since: Only return messages after this timestamp.
            include_expired: Include ephemeral messages that have expired.

        Returns:
            List of matching messages.

        Raises:
            ValueError: If agent is not a channel member.
        """
        if agent_id not in self._info.members:
            raise ValueError(f"{agent_id} is not a member of channel '{self.name}'")

        now = time.time()
        result: list[ChannelMessage] = []
        for msg in self._messages:
            if since is not None and msg.timestamp <= since:
                continue
            if not include_expired and not msg.is_alive(now):
                continue
            result.append(msg)
        return result

    def active_whispers(self, agent_id: Optional[str] = None) -> list[Whisper]:
        """Get active (non-expired) whispers in this channel.

        Args:
            agent_id: If provided, only return whispers targeting this agent.
        """
        now = time.time()
        result: list[Whisper] = []
        for w in self._whispers:
            w.tick(now)
            if w.state in (WhisperState.ACTIVE, WhisperState.FADING):
                if agent_id is None or w.matches(agent_id):
                    result.append(w)
        return result

    def prune(self) -> int:
        """Remove expired ephemeral messages and whispers.

        Returns:
            Number of items removed.
        """
        now = time.time()
        before_msgs = len(self._messages)
        before_ws = len(self._whispers)

        self._messages = [m for m in self._messages if m.is_alive(now)]
        self._whispers = [w for w in self._whispers if not w.is_expired(now)]

        return (before_msgs - len(self._messages)) + (before_ws - len(self._whispers))

    def message_count(self) -> int:
        """Total messages (including expired)."""
        return len(self._messages)

    def whisper_count(self) -> int:
        """Total whispers (including expired)."""
        return len(self._whispers)
