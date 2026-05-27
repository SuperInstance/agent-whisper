"""Agent Whisper — subtle influence, nudges, and indirect communication between agents."""

from .whisper import Whisper
from .nudge import NudgeEngine, NudgeType
from .channel import WhisperChannel, ChannelMessage
from .influence import InfluenceTracker, InfluenceRecord
from .ethics import EthicsGuard, ConsentRecord

__version__ = "0.1.0"
__all__ = [
    "Whisper",
    "NudgeEngine",
    "NudgeType",
    "WhisperChannel",
    "ChannelMessage",
    "InfluenceTracker",
    "InfluenceRecord",
    "EthicsGuard",
    "ConsentRecord",
]
