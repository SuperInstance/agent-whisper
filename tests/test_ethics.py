"""Tests for agent_whisper.ethics module."""

import time

import pytest

from agent_whisper.ethics import (
    ConsentStatus,
    EthicsGuard,
    EthicsViolation,
    InfluenceLimit,
)


class TestConsent:
    def test_grant_consent(self):
        g = EthicsGuard()
        rec = g.grant_consent("alice", "bob")
        assert rec.status == ConsentStatus.GRANTED
        assert g.has_consent("alice", "bob")

    def test_grant_with_scope(self):
        g = EthicsGuard()
        g.grant_consent("alice", "bob", scope=["whisper"])
        assert g.has_consent("alice", "bob", "whisper")
        assert not g.has_consent("alice", "bob", "nudge")

    def test_revoke_consent(self):
        g = EthicsGuard()
        g.grant_consent("alice", "bob")
        count = g.revoke_consent("alice", "bob")
        assert count == 1
        assert not g.has_consent("alice", "bob")

    def test_consent_expiry(self):
        g = EthicsGuard()
        rec = g.grant_consent("alice", "bob", ttl=0.01)
        time.sleep(0.02)
        assert not rec.is_valid()
        assert not g.has_consent("alice", "bob")


class TestEthicsCheck:
    def test_check_allowed(self):
        g = EthicsGuard()
        g.grant_consent("alice", "bob")
        assert g.check("alice", "bob", "whisper", strength=0.5)

    def test_check_no_consent(self):
        g = EthicsGuard()
        with pytest.raises(EthicsViolation, match="No consent"):
            g.check("alice", "bob", "whisper", strength=0.5)

    def test_check_invalid_strength(self):
        g = EthicsGuard()
        g.grant_consent("alice", "bob")
        with pytest.raises(EthicsViolation, match="Invalid strength"):
            g.check("alice", "bob", "whisper", strength=2.0)

    def test_check_cumulative_source_limit(self):
        limits = InfluenceLimit(max_influence_per_source=0.5)
        g = EthicsGuard(limits=limits)
        g.grant_consent("alice", "bob")
        g.check("alice", "bob", "whisper", strength=0.2, cumulative_from_source=0.3)
        with pytest.raises(EthicsViolation, match="Cumulative"):
            g.check("alice", "bob", "whisper", strength=0.3, cumulative_from_source=0.3)

    def test_check_total_limit(self):
        limits = InfluenceLimit(max_total_influence=1.0)
        g = EthicsGuard(limits=limits)
        g.grant_consent("alice", "bob")
        with pytest.raises(EthicsViolation, match="Total influence"):
            g.check("alice", "bob", "whisper", strength=0.5, cumulative_total=0.8)

    def test_check_nudge_rate_limit(self):
        limits = InfluenceLimit(max_nudges_per_hour=2)
        g = EthicsGuard(limits=limits)
        g.grant_consent("alice", "bob", scope=["nudge"])
        g.check("alice", "bob", "nudge", strength=0.1)
        g.check("alice", "bob", "nudge", strength=0.1)
        with pytest.raises(EthicsViolation, match="Rate limit"):
            g.check("alice", "bob", "nudge", strength=0.1)


class TestDefaultConsent:
    def test_default_consent_true(self):
        g = EthicsGuard(default_consent=True)
        assert g.has_consent("anyone", "anyone")

    def test_require_consent_false(self):
        limits = InfluenceLimit(require_consent=False)
        g = EthicsGuard(limits=limits)
        assert g.has_consent("anyone", "anyone")


class TestAuditLog:
    def test_audit_all(self):
        g = EthicsGuard()
        g.grant_consent("a", "b")
        g.check("a", "b", "whisper", strength=0.5)
        log = g.audit()
        assert len(log) == 1

    def test_audit_filtered(self):
        g = EthicsGuard()
        g.grant_consent("a", "b")
        g.grant_consent("c", "d")
        g.check("a", "b", "whisper", strength=0.5)
        g.check("c", "d", "nudge", strength=0.3)
        log = g.audit("b")
        assert len(log) == 1
        assert log[0]["source"] == "a"


class TestTransparencyReport:
    def test_none_level(self):
        limits = InfluenceLimit(transparency_level="none")
        g = EthicsGuard(limits=limits)
        g.grant_consent("a", "b")
        g.check("a", "b", "whisper", strength=0.5)
        report = g.transparency_report("b")
        assert report["details"] == "hidden"

    def test_summary_level(self):
        limits = InfluenceLimit(transparency_level="summary")
        g = EthicsGuard(limits=limits)
        g.grant_consent("a", "b")
        g.check("a", "b", "whisper", strength=0.5)
        report = g.transparency_report("b")
        assert "by_source" in report
        assert "a" in report["by_source"]

    def test_full_level(self):
        limits = InfluenceLimit(transparency_level="full")
        g = EthicsGuard(limits=limits)
        g.grant_consent("a", "b")
        g.check("a", "b", "whisper", strength=0.5)
        report = g.transparency_report("b")
        assert "events" in report
        assert len(report["events"]) == 1


class TestClear:
    def test_clear(self):
        g = EthicsGuard()
        g.grant_consent("a", "b")
        g.check("a", "b", "whisper", strength=0.5)
        g.clear()
        assert len(g.audit()) == 0
        assert not g.has_consent("a", "b")
