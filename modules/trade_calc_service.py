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

    processing_cost = 3.2 + max(0.0, sio2_grade - 2.0) * 0.9
    management_cost = max(1.5, target_price * 0.015)

    if caf2_grade < 75:
        actual_price = max(0.0, target_price - impurity_penalty - 12.0)
        quality_loss = 12.0
        unit_operating_cost = logistics_cost + processing_cost + management_cost
        break_even_quote = actual_price - unit_operating_cost

        cost_breakdown = {
            "物流成本": round(logistics_cost, 2),
            "杂质扣罚": round(impurity_penalty, 2),
            "加工成本": round(processing_cost, 2),
            "管理成本": round(management_cost, 2),
            "质量折损": round(quality_loss, 2),
        }
        return TradeCalcResult(
            passed_grade_gate=False,
            risk_level="高风险",
            risk_hint="CaF2低于75%，建议拒收或重新谈判质量条款。",
            recommended_strategy="建议放弃或要求提品后再议",
            profit_change_reason="利润受低品位触发的质量折损、杂质扣罚与全链路成本共同挤压。",
            decision_advice="当前条件下不建议成交；如必须推进，需先提升品位并显著压低采购价。",
            actual_deal_price=round(actual_price, 2),
            quote_selected=0.0,
            optimal_quote=0.0,
            suggested_quote_low=0.0,
            suggested_quote_high=0.0,
            negotiation_space=0.0,
            break_even_quote=round(break_even_quote, 2),
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
    quality_risk_cost = 1.2

    if 75 <= caf2_grade < 80:
        grade_adjustment = -7.0
        risk_level = "中风险"
        deal_probability = 0.62
        quality_risk_cost = 2.6
    elif caf2_grade >= 88:
        grade_adjustment = 4.0
        deal_probability = 0.90
        quality_risk_cost = 0.8

    actual_deal_price = max(0.0, target_price + grade_adjustment - impurity_penalty)

    unit_operating_cost = logistics_cost + processing_cost + management_cost + quality_risk_cost
    break_even_quote = actual_deal_price - unit_operating_cost

    market_anchor_quote = actual_deal_price * 0.72
    quality_discount = max(0.0, 82 - caf2_grade) * 0.4
    impurity_discount = max(0.0, sio2_grade - 2.0) * 0.5
    cost_pressure_discount = logistics_cost * 0.2

    suggested_quote_high = max(0.0, market_anchor_quote - quality_discount - impurity_discount - cost_pressure_discount)
    quote_span = max(3.0, actual_deal_price * 0.05)
    suggested_quote_low = max(0.0, suggested_quote_high - quote_span)
    negotiation_space = max(0.0, suggested_quote_high - suggested_quote_low)
    quote_selected = (suggested_quote_low + suggested_quote_high) / 2

    profit_per_ton = actual_deal_price - unit_operating_cost - quote_selected
    total_profit = profit_per_ton * volume_ton

    profit_range_low = actual_deal_price - unit_operating_cost - suggested_quote_high
    profit_range_high = actual_deal_price - unit_operating_cost - suggested_quote_low

    trend_points: List[Dict[str, float]] = []
    min_quote = max(0.0, suggested_quote_low - quote_span)
    max_quote = suggested_quote_high + quote_span
    step = max(1.0, quote_span / 4)

    current = min_quote
    max_profit = None
    optimal_quote = min_quote
    while current <= max_quote + 1e-9:
        p = actual_deal_price - unit_operating_cost - current
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
                "profit_per_ton": round(adj_price - unit_operating_cost - quote_selected, 2),
            }
        )

    cost_breakdown = {
        "物流成本": round(logistics_cost, 2),
        "杂质扣罚": round(impurity_penalty, 2),
        "加工成本": round(processing_cost, 2),
        "管理成本": round(management_cost, 2),
        "质量风险成本": round(quality_risk_cost, 2),
    }

    result_interpretation = (
        f"单吨利润约 {profit_per_ton:.2f} USD（约 {profit_per_ton * exchange_rate:.2f} RMB），"
        f"总利润约 {total_profit:.2f} USD（约 {total_profit * exchange_rate:.2f} RMB）。"
    )
    logic_basis = (
        "先按CaF2与SiO2修正成交价，再叠加物流/加工/管理/质量风险成本，"
        f"报价区间由市场锚点与成本压力共同决定；最优报价点约为 {optimal_quote:.2f} USD/吨。"
    )
    details = (
        f"实际成交价={target_price:.2f}+{grade_adjustment:.2f}-{impurity_penalty:.2f}={actual_deal_price:.2f}；"
        f"单位综合成本={unit_operating_cost:.2f}；建议报价区间 {suggested_quote_low:.2f}~{suggested_quote_high:.2f} USD/吨。"
    )

    risk_hint = "建议在推荐区间内谈判，若报价高于盈亏平衡点将快速侵蚀利润。"
    if risk_level == "中风险":
        risk_hint = "当前为折价交易区间，建议增加质量复检条款并压低报价。"

    return TradeCalcResult(
        passed_grade_gate=True,
        risk_level=risk_level,
        risk_hint=risk_hint,
        recommended_strategy="在推荐区间内谈判并锁定质量条款" if risk_level == "低风险" else "优先压价并补充复检条款",
        profit_change_reason="利润由成交价修正、物流/加工/管理/质量风险成本和采购报价共同决定，任一输入变化都会联动影响单吨利润。",
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
