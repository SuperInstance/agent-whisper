"""Tests for agent_whisper.influence module."""

import pytest

from agent_whisper.influence import InfluenceTracker


class TestInfluenceRecording:
    def test_record_basic(self):
        t = InfluenceTracker()
        rec = t.record("alice", "bob", "whisper", "w1", strength=0.5)
        assert rec.source == "alice"
        assert rec.target == "bob"
        assert rec.strength == 0.5

    def test_invalid_strength(self):
        t = InfluenceTracker()
        with pytest.raises(ValueError, match="strength"):
            t.record("a", "b", "whisper", "w1", strength=2.0)

    def test_record_count(self):
        t = InfluenceTracker()
        t.record("a", "b", "whisper", "w1", strength=0.3)
        t.record("b", "c", "nudge", "n1", strength=0.4)
        assert t.record_count() == 2


class TestInfluenceRecordsFor:
    def test_inbound(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.5)
        t.record("carol", "dave", "nudge", "n1", strength=0.3)
        recs = t.records_for("bob", "inbound")
        assert len(recs) == 1
        assert recs[0].source == "alice"

    def test_outbound(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.5)
        recs = t.records_for("alice", "outbound")
        assert len(recs) == 1

    def test_both(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.5)
        t.record("bob", "alice", "nudge", "n1", strength=0.3)
        recs = t.records_for("alice", "both")
        assert len(recs) == 2

    def test_since_filter(self):
        import time
        t = InfluenceTracker()
        t.record("a", "b", "whisper", "w1", strength=0.5)
        time.sleep(0.01)
        cutoff = time.time()
        t.record("a", "b", "nudge", "n1", strength=0.3)
        recs = t.records_for("b", "inbound", since=cutoff)
        assert len(recs) == 1
        assert recs[0].influence_type == "nudge"


class TestInfluenceSummary:
    def test_summary_inbound_outbound(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.7)
        t.record("carol", "bob", "nudge", "n1", strength=0.4)
        s = t.summary("bob")
        assert s.total_inbound == pytest.approx(1.1)
        assert s.influence_count == 2

    def test_summary_by_type(self):
        t = InfluenceTracker()
        t.record("a", "b", "whisper", "w1", strength=0.5)
        t.record("a", "b", "nudge", "n1", strength=0.3)
        s = t.summary("b")
        assert s.by_type["whisper"] == pytest.approx(0.5)
        assert s.by_type["nudge"] == pytest.approx(0.3)

    def test_summary_top_influencer(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.7)
        t.record("carol", "bob", "nudge", "n1", strength=0.2)
        s = t.summary("bob")
        assert s.top_influencer == "alice"

    def test_summary_outbound(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.5)
        t.record("alice", "carol", "nudge", "n1", strength=0.3)
        s = t.summary("alice")
        assert s.total_outbound == pytest.approx(0.8)


class TestInfluenceBetween:
    def test_influence_between(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.5)
        t.record("alice", "bob", "nudge", "n1", strength=0.3)
        t.record("carol", "bob", "whisper", "w2", strength=0.2)
        assert t.influence_between("alice", "bob") == pytest.approx(0.8)

    def test_influence_between_none(self):
        t = InfluenceTracker()
        assert t.influence_between("a", "b") == 0.0


class TestTopInfluencers:
    def test_top_influencers(self):
        t = InfluenceTracker()
        t.record("alice", "bob", "whisper", "w1", strength=0.9)
        t.record("carol", "bob", "nudge", "n1", strength=0.3)
        ranked = t.top_influencers()
        assert ranked[0][0] == "alice"
        assert ranked[0][1] == pytest.approx(0.9)


class TestMaxRecords:
    def test_eviction(self):
        t = InfluenceTracker(max_records=5)
        for i in range(10):
            t.record("a", "b", "whisper", f"w{i}", strength=0.1)
        assert t.record_count() == 5


class TestInfluenceClear:
    def test_clear(self):
        t = InfluenceTracker()
        t.record("a", "b", "whisper", "w1", strength=0.5)
        t.clear()
        assert t.record_count() == 0
