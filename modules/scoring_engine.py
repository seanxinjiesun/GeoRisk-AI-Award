from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


WEIGHTS = {
    "geological_potential": 0.30,
    "data_integrity": 0.20,
    "project_stage": 0.20,
    "risk_factor": 0.30,
}


@dataclass
class ScoreResult:
    total_score: float
    weighted_scores: Dict[str, float]
    penalties: List[str]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def calculate_geo_risk_score(inputs: Dict[str, float], has_drilling_data: bool, non_systematic_sampling: bool) -> ScoreResult:
    weighted = {}
    penalties: List[str] = []

    for key, weight in WEIGHTS.items():
        raw = _clamp(float(inputs.get(key, 0)))
        weighted[key] = raw * weight

    score = sum(weighted.values())

    if not has_drilling_data:
        score -= 20
        penalties.append("无钻孔数据：降20分，且不具备资产估值条件")

    if non_systematic_sampling:
        score -= 8
        penalties.append("非系统采样：降8分，数据可信度受限")

    score = _clamp(score)

    return ScoreResult(
        total_score=round(score, 2),
        weighted_scores={k: round(v, 2) for k, v in weighted.items()},
        penalties=penalties,
    )
