"""Tests for agent_whisper.channel module."""

import time

import pytest

from agent_whisper.channel import WhisperChannel, ChannelMessage
from agent_whisper.whisper import Whisper


class TestChannelMembership:
    def test_subscribe(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        assert "alice" in ch.members

    def test_double_subscribe(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("alice")
        assert ch.members.count("alice") == 1

    def test_unsubscribe(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        assert ch.unsubscribe("alice")
        assert "alice" not in ch.members

    def test_unsubscribe_nonmember(self):
        ch = WhisperChannel("test")
        assert not ch.unsubscribe("nobody")


class TestChannelMessaging:
    def test_send_message(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        msg = ch.send("alice", "hello")
        assert msg.content == "hello"
        assert msg.sender == "alice"
        assert msg.channel == "test"

    def test_send_nonmember_raises(self):
        ch = WhisperChannel("test")
        with pytest.raises(ValueError, match="not a member"):
            ch.send("stranger", "hello")

    def test_inbox(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("bob")
        ch.send("alice", "hi bob")
        msgs = ch.inbox("bob")
        assert len(msgs) == 1
        assert msgs[0].content == "hi bob"

    def test_inbox_nonmember_raises(self):
        ch = WhisperChannel("test")
        with pytest.raises(ValueError, match="not a member"):
            ch.inbox("nobody")

    def test_inbox_since_filter(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("bob")
        msg1 = ch.send("alice", "old")
        time.sleep(0.01)
        cutoff = time.time()
        ch.send("alice", "new")
        msgs = ch.inbox("bob", since=cutoff)
        assert len(msgs) == 1
        assert msgs[0].content == "new"


class TestEphemeralMessages:
    def test_ephemeral_expires(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("bob")
        ch.send("alice", "gone soon", ephemeral=True, ttl=0.01)
        time.sleep(0.02)
        msgs = ch.inbox("bob")
        assert len(msgs) == 0

    def test_ephemeral_included_with_flag(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("bob")
        ch.send("alice", "gone soon", ephemeral=True, ttl=0.01)
        time.sleep(0.02)
        msgs = ch.inbox("bob", include_expired=True)
        assert len(msgs) == 1

    def test_persistent_survives(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.subscribe("bob")
        ch.send("alice", "stays forever", ephemeral=False)
        time.sleep(0.01)
        msgs = ch.inbox("bob")
        assert len(msgs) == 1


class TestChannelWhispers:
    def test_whisper_through_channel(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        w = Whisper(content="subtle hint", intensity=0.7, source="alice", target="*")
        msg = ch.whisper(w)
        assert msg.content == "subtle hint"
        assert msg.metadata["whisper_id"] == w.id

    def test_active_whispers(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        w = Whisper(content="hint", intensity=0.8, duration=60.0, source="alice")
        w.activate()
        ch.whisper(w)
        active = ch.active_whispers()
        assert len(active) == 1


class TestChannelPrune:
    def test_prune_expired(self):
        ch = WhisperChannel("test")
        ch.subscribe("alice")
        ch.send("alice", "ephemeral", ephemeral=True, ttl=0.01)
        time.sleep(0.02)
        removed = ch.prune()
        assert removed >= 1
        assert ch.message_count() == 0


class TestChannelMessageSerialization:
    def test_to_dict(self):
        msg = ChannelMessage(channel="c", sender="a", content="hi")
        d = msg.to_dict()
        assert d["channel"] == "c"
        assert d["content"] == "hi"
