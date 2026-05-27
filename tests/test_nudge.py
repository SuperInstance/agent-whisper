"""Tests for agent_whisper.nudge module."""

import pytest

from agent_whisper.nudge import NudgeEngine, NudgeType


class TestNudgeCreation:
    def test_create_nudge(self):
        engine = NudgeEngine()
        n = engine.create_nudge(
            NudgeType.ANCHORING, "Most choose A", "agent-1", strength=0.3
        )
        assert n.nudge_type == NudgeType.ANCHORING
        assert n.content == "Most choose A"
        assert n.target == "agent-1"
        assert n.strength == 0.3

    def test_invalid_strength(self):
        engine = NudgeEngine()
        with pytest.raises(ValueError, match="strength"):
            engine.create_nudge(NudgeType.FRAMING, "x", "a", strength=2.0)


class TestNudgeApplication:
    def test_apply_basic(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.DEFAULT_SETTING, "default=X", "a1", strength=0.5)
        result = engine.apply(n)
        assert result.applied
        assert result.estimated_influence > 0

    def test_apply_with_anchoring_susceptible(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.ANCHORING, "ref=10", "a1", strength=0.5)
        result = engine.apply(n, target_preferences={"decisiveness": 0.1})
        assert result.estimated_influence > 0.5  # boosted

    def test_apply_with_social_proof_conformist(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.SOCIAL_PROOF, "everyone does X", "a1", strength=0.4)
        result = engine.apply(n, target_preferences={"conformity": 0.9})
        assert result.estimated_influence > 0.4

    def test_apply_with_default_setting_lazy(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.DEFAULT_SETTING, "default=opt1", "a1", strength=0.3)
        result = engine.apply(n, target_preferences={"laziness": 0.9})
        assert result.estimated_influence > 0.3

    def test_apply_with_scarcity_fomo(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.SCARCITY, "only 2 left!", "a1", strength=0.5)
        result = engine.apply(n, target_preferences={"fomo": 0.9})
        assert result.estimated_influence > 0.5

    def test_influence_capped_at_1(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.SOCIAL_PROOF, "x", "a1", strength=0.95)
        result = engine.apply(n, target_preferences={"conformity": 0.99})
        assert result.estimated_influence <= 1.0


class TestNudgeManagement:
    def test_revoke(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.FRAMING, "x", "a1")
        engine.apply(n)
        assert engine.revoke(n.id)
        assert len(engine.active_nudges()) == 0

    def test_revoke_nonexistent(self):
        engine = NudgeEngine()
        assert not engine.revoke("nope")

    def test_active_nudges_filter_by_target(self):
        engine = NudgeEngine()
        n1 = engine.create_nudge(NudgeType.FRAMING, "x", "a1")
        n2 = engine.create_nudge(NudgeType.ANCHORING, "y", "a2")
        engine.apply(n1)
        engine.apply(n2)
        assert len(engine.active_nudges("a1")) == 1

    def test_max_active_nudges(self):
        engine = NudgeEngine(max_active_nudges=3)
        for i in range(5):
            n = engine.create_nudge(NudgeType.FRAMING, f"n{i}", f"a{i}")
            engine.apply(n)
        assert len(engine.active_nudges()) == 3

    def test_history(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.FRAMING, "x", "a1")
        engine.apply(n)
        h = engine.history()
        assert len(h) == 1

    def test_clear(self):
        engine = NudgeEngine()
        n = engine.create_nudge(NudgeType.FRAMING, "x", "a1")
        engine.apply(n)
        engine.clear()
        assert len(engine.active_nudges()) == 0
        assert len(engine.history()) == 0
