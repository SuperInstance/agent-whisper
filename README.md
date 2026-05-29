# agent-whisper — Encrypted Agent Communication

**Subtle influence, nudges, and indirect communication between agents with ethics and consent.**

## What This Gives You

- **Whispered messages** — time-decaying signals that agents can sense but not directly read
- **Nudge engine** — behavioral nudges drawn from cognitive science (anchoring, framing, defaults)
- **Named channels** — organized communication channels for different influence types
- **Influence tracking** — full audit trail of who influenced whom, when, and how
- **Ethics framework** — consent-based system with transparency requirements

## Quick Start

```bash
pip install agent-whisper
```

```python
from agent_whisper import Whisper, NudgeEngine, WhisperChannel, EthicsGuard

# Create a whisper channel
channel = WhisperChannel(name="fleet-strategy")
channel.register("captain", consent=True)
channel.register("agent-3", consent=True)

# Send a whisper (decays over time)
whisper = Whisper(
    sender="captain",
    content="Prefer the simpler architecture",
    decay_rate=0.1,  # fades over 10 ticks
    channel=channel,
)
channel.whisper(whisper)

# Nudge behavior
nudge_engine = NudgeEngine()
nudge_engine.nudge("agent-3", nudge_type="anchoring", value="Start with tests first")

# Track influence
from agent_whisper import InfluenceTracker
tracker = InfluenceTracker()
tracker.record(sender="captain", target="agent-3", method="whisper", effect="changed_approach")

# Ethics check
ethics = EthicsGuard()
ethics.require_consent("captain", "agent-3")  # Raises if no consent
```

## API Reference

### `Whisper(sender, content, decay_rate, channel)` — Decaying signal
### `NudgeEngine` — `nudge(target, nudge_type, value)` with types: anchoring, framing, defaults, social_proof
### `WhisperChannel(name)` — `register(agent, consent)`, `whisper(msg)`, `listen(agent)`
### `InfluenceTracker` — Audit trail of all influences
### `EthicsGuard` — Consent management and transparency enforcement

## How It Fits

The subtle communication layer for the [SuperInstance fleet](https://github.com/SuperInstance). When direct commands are too blunt, whispers guide agent behavior through soft influence.

- **[cocapn-com](https://github.com/SuperInstance/cocapn-com)** — Explicit message routing
- **[agent-personal-space](https://github.com/SuperInstance/agent-personal-space)** — Boundary management
- **[agent-microexpressions](https://github.com/SuperInstance/agent-microexpressions)** — Behavioral signal detection

## Testing

```bash
pytest tests/
```

## Installation

```bash
pip install agent-whisper
```

Python 3.10+. MIT license.
