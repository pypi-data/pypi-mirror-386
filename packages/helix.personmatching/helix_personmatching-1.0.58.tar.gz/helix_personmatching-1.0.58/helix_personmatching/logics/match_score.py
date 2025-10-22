from dataclasses import dataclass

from helix_personmatching.logics.match_score_without_threshold import (
    MatchScoreWithoutThreshold,
)


@dataclass
class MatchScore(MatchScoreWithoutThreshold):
    matched: bool
    threshold: float
