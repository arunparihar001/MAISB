"""Channel reputation engine for Phase 2."""
from dataclasses import dataclass


@dataclass
class ReputationStats:
    event_count: int = 0
    blocked_count: int = 0
    review_count: int = 0

    @property
    def bad_ratio(self) -> float:
        if self.event_count <= 0:
            return 0.0
        return (self.blocked_count + 0.5 * self.review_count) / self.event_count


class ReputationEngine:
    """Calculate reputation penalty from historical channel outcomes."""

    def adjustment(self, stats: ReputationStats) -> float:
        return max(-0.25, -stats.bad_ratio * 0.25)
