from __future__ import annotations

from typing import Dict, List


def build_decision_codes(signals: Dict[str, bool]) -> List[str]:
    codes: List[str] = []

    if signals.get("credibility_issue", False):
        codes.append("D1")
    if signals.get("abnormal_orebody_params", False):
        codes.append("D2")
    if signals.get("insufficient_exploration_level", False):
        codes.append("D3")
    if signals.get("fraud_packaging_pattern", False):
        codes.append("D4")

    return codes


def final_investment_decision(score: float, has_drilling_data: bool, risk_level: str) -> str:
    if not has_drilling_data:
        return "❌ 建议放弃（当前不具备资产估值条件）"

    if risk_level in ["高风险", "极高风险"]:
        return "❌ 建议放弃"

    if score >= 75:
        return "✅ 建议推进"
    if score >= 55:
        return "⚠️ 谨慎评估"
    return "❌ 建议放弃"
