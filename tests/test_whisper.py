"""Tests for agent_whisper.whisper module."""

import time

from agent_whisper.whisper import Whisper, WhisperState


class TestWhisperCreation:
    def test_basic_creation(self):
        w = Whisper(content="hello", intensity=0.5, target="agent-1")
        assert w.content == "hello"
        assert w.intensity == 0.5
        assert w.target == "agent-1"
        assert w.state == WhisperState.PENDING
        assert w.id

    def test_default_values(self):
        w = Whisper(content="ping")
        assert w.intensity == 0.5
        assert w.target == "*"
        assert w.duration == 60.0
        assert w.decay_rate == 0.1
        assert w.source is None

    def test_invalid_intensity(self):
        import pytest
        with pytest.raises(ValueError, match="intensity"):
            Whisper(content="x", intensity=1.5)

    def test_invalid_decay_rate(self):
        import pytest
        with pytest.raises(ValueError, match="decay_rate"):
            Whisper(content="x", decay_rate=-0.1)

    def test_negative_duration(self):
        import pytest
        with pytest.raises(ValueError, match="duration"):
            Whisper(content="x", duration=-1)


class TestWhisperState:
    def test_activate(self):
        w = Whisper(content="hello")
        w.activate()
        assert w.state == WhisperState.ACTIVE

    def test_activate_only_from_pending(self):
        w = Whisper(content="hello")
        w.activate()
        w.activate()  # no-op from active
        assert w.state == WhisperState.ACTIVE

    def test_revoke(self):
        w = Whisper(content="hello")
        w.activate()
        w.revoke()
        assert w.state == WhisperState.REVOKED


class TestWhisperIntensity:
    def test_full_intensity_during_duration(self):
        w = Whisper(content="x", intensity=0.8, duration=60.0)
        w.activate()
        assert w.current_intensity(now=w.created_at + 30) == 0.8

    def test_zero_intensity_when_pending(self):
        w = Whisper(content="x", intensity=0.8)
        assert w.current_intensity() == 0.0

    def test_zero_intensity_when_revoked(self):
        w = Whisper(content="x", intensity=0.8)
        w.activate()
        w.revoke()
        assert w.current_intensity() == 0.0

    def test_decay_after_duration(self):
        w = Whisper(content="x", intensity=1.0, duration=10.0, decay_rate=0.5)
        w.activate()
        # After duration: decayed = 1.0 * (1 - 0.5)^(elapsed/duration)
        after = w.created_at + 20.0  # 10s past duration, elapsed/duration = 2.0
        intensity = w.current_intensity(now=after)
        assert intensity < 1.0
        assert intensity > 0.0

    def test_eventually_expires(self):
        w = Whisper(content="x", intensity=0.5, duration=1.0, decay_rate=0.9)
        w.activate()
        far_future = w.created_at + 1000.0
        assert w.current_intensity(now=far_future) < 0.001


class TestWhisperTick:
    def test_tick_to_fading(self):
        w = Whisper(content="x", intensity=1.0, duration=1.0, decay_rate=0.8)
        w.activate()
        # After 2s: decayed = 1.0 * (1-0.8)^(2/1) = 0.04 → fading
        state = w.tick(now=w.created_at + 2.0)
        assert state == WhisperState.FADING

    def test_tick_to_expired(self):
        w = Whisper(content="x", intensity=0.5, duration=0.001, decay_rate=0.99)
        w.activate()
        state = w.tick(now=w.created_at + 100.0)
        assert state == WhisperState.EXPIRED


class TestWhisperMatching:
    def test_broadcast_matches_all(self):
        w = Whisper(content="x", target="*")
        assert w.matches("anyone")

    def test_targeted_matches(self):
        w = Whisper(content="x", target="agent-1")
        assert w.matches("agent-1")
        assert not w.matches("agent-2")


class TestWhisperSerialization:
    def test_to_dict_and_back(self):
        w = Whisper(content="test", intensity=0.7, target="a1", source="a2")
        w.activate()
        d = w.to_dict()
        w2 = Whisper.from_dict(d)
        assert w2.content == w.content
        assert w2.intensity == w.intensity
        assert w2.target == w.target
        assert w2.source == w.source
        assert w2.state == w.state
        assert w2.id == w.id
