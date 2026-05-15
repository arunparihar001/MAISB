"""Channel trust profile definitions."""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ChannelTrustProfile:
    channel: str
    base_score: float
    risk_notes: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {"channel": self.channel, "base_score": self.base_score, "risk_notes": self.risk_notes, "controls": self.controls}
