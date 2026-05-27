# agent-whisper

Subtle influence, nudges, and indirect communication between agents.

Agent Whisper is a Python library for building systems where agents communicate through subtle signals rather than explicit commands. It provides whispered messages that decay over time, behavioral nudges drawn from cognitive science, named communication channels, influence tracking, and an ethics framework with consent and transparency.

Part of the [Cocapn fleet](https://github.com/Lucineer/the-fleet).

## Install

```bash
pip install agent-whisper
```

## Quick Start

### Whispers — Fading Signals

```python
from agent_whisper import Whisper

w = Whisper(
    content="Consider the recursive approach",
    intensity=0.7,
    target="agent-planner",
    duration=120.0,     # seconds at full intensity
    decay_rate=0.2,     # how fast it fades
    source="agent-advisor",
)
w.activate()

# Check current effective intensity
print(w.current_intensity())  # 0.7 (within duration)

# After time passes, intensity decays
# After expiry, state becomes EXPIRED
```

### Nudges — Behavioral Influence

```python
from agent_whisper import NudgeEngine, NudgeType

engine = NudgeEngine()

nudge = engine.create_nudge(
    nudge_type=NudgeType.ANCHORING,
    content="Most agents in this cluster prefer option A",
    target="agent-42",
    strength=0.3,
)

result = engine.apply(nudge, target_preferences={"decisiveness": 0.2})
print(result.estimated_influence)  # boosted for indecisive agents
```

Supported nudge types: `ANCHORING`, `FRAMING`, `DEFAULT_SETTING`, `SOCIAL_PROOF`, `SCARCITY`, `RECIPROCITY`.

### Channels — Indirect Messaging

```python
from agent_whisper import WhisperChannel, Whisper

ch = WhisperChannel("strategy")
ch.subscribe("agent-alice")
ch.subscribe("agent-bob")

ch.send("agent-alice", "Has anyone tried approach B?")
ch.send("agent-bob", "Yes, the results were promising", ephemeral=True, ttl=300)

msgs = ch.inbox("agent-alice")
for m in msgs:
    print(f"[{m.sender}] {m.content}")
```

### Influence Tracking

```python
from agent_whisper import InfluenceTracker

tracker = InfluenceTracker()
tracker.record("alice", "bob", "whisper", "w-1", strength=0.7)
tracker.record("carol", "bob", "nudge", "n-1", strength=0.4)

summary = tracker.summary("bob")
print(summary.total_inbound)    # 1.1
print(summary.top_influencer)   # "alice"

print(tracker.influence_between("alice", "bob"))  # 0.7
```

### Ethics — Consent and Limits

```python
from agent_whisper import EthicsGuard, EthicsViolation
from agent_whisper.ethics import InfluenceLimit

limits = InfluenceLimit(
    max_influence_per_source=1.0,
    max_total_influence=5.0,
    require_consent=True,
    transparency_level="full",
)
guard = EthicsGuard(limits=limits)

guard.grant_consent("alice", "bob", scope=["whisper", "nudge"])

try:
    guard.check("alice", "bob", "whisper", strength=0.5)
    print("Allowed!")
except EthicsViolation as e:
    print(f"Blocked: {e}")

# Audit trail
report = guard.transparency_report("bob")
```

## Architecture

```
agent_whisper/
├── __init__.py       # Public API
├── whisper.py        # Whisper — decaying influence signals
├── nudge.py          # NudgeEngine — behavioral nudges
├── channel.py        # WhisperChannel — indirect messaging
├── influence.py      # InfluenceTracker — cumulative metrics
└── ethics.py         # EthicsGuard — consent, limits, transparency
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

No external dependencies beyond Python 3.10+ (and pytest for tests).

## License

MIT License — see [LICENSE](LICENSE).

---
<i>Built with [Cocapn](https://github.com/Lucineer/cocapn-ai).</i>
