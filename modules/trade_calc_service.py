from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TradeCalcResult:
    passed_grade_gate: bool
    risk_level: str
    risk_hint: str
    recommended_strategy: str
    profit_change_reason: str
    decision_advice: str
    actual_deal_price: float
    quote_selected: float
    optimal_quote: float
    suggested_quote_low: float
    suggested_quote_high: float
    negotiation_space: float
    break_even_quote: float
    profit_per_ton: float
    total_profit: float
    profit_range_low: float
    profit_range_high: float
    deal_probability: float
    cost_breakdown: Dict[str, float]
    trend_points: List[Dict[str, float]]
    sensitivity_points: List[Dict[str, float]]
    result_interpretation: str
    logic_basis: str
    details: str


def calculate_trade(
    caf2_grade: float,
    sio2_grade: float,
    logistics_cost: float,
    target_price: float,
    exchange_rate: float,
    volume_ton: float,
) -> TradeCalcResult:
    logistics_cost = max(0.0, logistics_cost)
    volume_ton = max(0.0, volume_ton)
    exchange_rate = exchange_rate if exchange_rate > 0 else 7.2

    impurity_penalty = max(0.0, (sio2_grade - 2.0) * 2.0)

    if caf2_grade < 75:
        actual_price = max(0.0, target_price - impurity_penalty - 12.0)
        cost_breakdown = {
            "物流成本": round(logistics_cost, 2),
            "杂质扣罚": round(impurity_penalty, 2),
            "质量折损": 12.0,
        }
        return TradeCalcResult(
            passed_grade_gate=False,
            risk_level="高风险",
            risk_hint="CaF2低于75%，建议拒收或重新谈判质量条款。",
            recommended_strategy="建议放弃或要求提品后再议",
            profit_change_reason="利润主要受低品位触发质量折损、杂质扣罚及物流成本三项共同压缩。",
            decision_advice="当前条件下不建议成交；如必须推进，需先提升品位或大幅压低收购价。",
            actual_deal_price=round(actual_price, 2),
            quote_selected=0.0,
            optimal_quote=0.0,
            suggested_quote_low=0.0,
            suggested_quote_high=0.0,
            negotiation_space=0.0,
            break_even_quote=round(actual_price - logistics_cost, 2),
            profit_per_ton=0.0,
            total_profit=0.0,
            profit_range_low=0.0,
            profit_range_high=0.0,
            deal_probability=0.18,
            cost_breakdown=cost_breakdown,
            trend_points=[],
            sensitivity_points=[],
            result_interpretation="品位触发拒收阈值，继续成交可能导致亏损与质量争议。",
            logic_basis="规则：CaF2<75 判定高风险拒收。",
            details="不满足最低品位交易条件，建议放弃或要求提品后再议。",
        )

    grade_adjustment = 0.0
    risk_level = "低风险"
    deal_probability = 0.84
    if 75 <= caf2_grade < 80:
        grade_adjustment = -7.0
        risk_level = "中风险"
        deal_probability = 0.62
    elif caf2_grade >= 88:
        grade_adjustment = 4.0
        deal_probability = 0.9

    actual_deal_price = target_price + grade_adjustment - impurity_penalty

    risk_buffer = 8.0 if caf2_grade >= 80 else 6.0
    suggested_quote_high = actual_deal_price - logistics_cost - risk_buffer
    suggested_quote_low = suggested_quote_high - 5.0
    negotiation_space = max(0.0, suggested_quote_high - suggested_quote_low)
    quote_selected = (suggested_quote_low + suggested_quote_high) / 2

    profit_per_ton = actual_deal_price - logistics_cost - quote_selected
    total_profit = profit_per_ton * volume_ton

    break_even_quote = actual_deal_price - logistics_cost
    profit_range_low = actual_deal_price - logistics_cost - suggested_quote_high
    profit_range_high = actual_deal_price - logistics_cost - suggested_quote_low

    trend_points: List[Dict[str, float]] = []
    min_quote = max(0.0, suggested_quote_low - 6)
    max_quote = suggested_quote_high + 6
    step = 1.5
    current = min_quote
    max_profit = None
    optimal_quote = min_quote
    while current <= max_quote + 1e-9:
        p = actual_deal_price - logistics_cost - current
        trend_points.append({"quote": round(current, 2), "profit": round(p, 2)})
        if max_profit is None or p > max_profit:
            max_profit = p
            optimal_quote = current
        current += step

    sensitivity_points: List[Dict[str, float]] = []
    for delta in [-5, -2, 0, 2, 5]:
        adj_price = actual_deal_price + delta
        sensitivity_points.append(
            {
                "scenario": f"成交价{delta:+}USD",
                "profit_per_ton": round(adj_price - logistics_cost - quote_selected, 2),
            }
        )

    cost_breakdown = {
        "物流成本": round(logistics_cost, 2),
        "杂质扣罚": round(impurity_penalty, 2),
        "风险缓冲": round(risk_buffer, 2),
    }

    result_interpretation = (
        f"单吨利润约 {profit_per_ton:.2f} USD（约 {profit_per_ton * exchange_rate:.2f} RMB），"
        f"总利润约 {total_profit:.2f} USD（约 {total_profit * exchange_rate:.2f} RMB）。"
    )
    logic_basis = (
        f"依据CaF2阈值分段、SiO2扣价、物流成本和风控缓冲计算；最优报价点约为 {optimal_quote:.2f} USD/吨。"
    )
    details = (
        f"实际成交价={target_price:.2f}+{grade_adjustment:.2f}-{impurity_penalty:.2f}={actual_deal_price:.2f}；"
        f"建议报价区间 {suggested_quote_low:.2f}~{suggested_quote_high:.2f} USD/吨。"
    )

    risk_hint = "建议在推荐区间内谈判，若报价高于盈亏平衡点将快速侵蚀利润。"
    if risk_level == "中风险":
        risk_hint = "当前为折价交易区间，建议增加质量复检条款并压低报价。"

    return TradeCalcResult(
        passed_grade_gate=True,
        risk_level=risk_level,
        risk_hint=risk_hint,
        recommended_strategy="在推荐区间内谈判并锁定质量条款" if risk_level == "低风险" else "优先压价并补充复检条款",
        profit_change_reason="利润受品位分段、SiO2扣价、物流成本和汇率共同影响；其中报价每上升1美元会直接压缩同额单吨利润。",
        decision_advice=(
            "建议在推荐区间内报价并优先锁定质量与复检条款，若对方报价高于盈亏平衡点应终止成交。"
            if risk_level == "低风险" else
            "当前处于折价区，建议先谈判降价并增加复检条款，无法改善条件时应谨慎或放弃。"
        ),
        actual_deal_price=round(actual_deal_price, 2),
        quote_selected=round(quote_selected, 2),
        optimal_quote=round(optimal_quote, 2),
        suggested_quote_low=round(suggested_quote_low, 2),
        suggested_quote_high=round(suggested_quote_high, 2),
        negotiation_space=round(negotiation_space, 2),
        break_even_quote=round(break_even_quote, 2),
        profit_per_ton=round(profit_per_ton, 2),
        total_profit=round(total_profit, 2),
        profit_range_low=round(profit_range_low, 2),
        profit_range_high=round(profit_range_high, 2),
        deal_probability=round(deal_probability, 2),
        cost_breakdown=cost_breakdown,
        trend_points=trend_points,
        sensitivity_points=sensitivity_points,
        result_interpretation=result_interpretation,
        logic_basis=logic_basis,
        details=details,
    )
