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
    buy_price: float,
    sell_price: float,
    exchange_rate: float,
    volume_ton: float,
) -> TradeCalcResult:
    logistics_cost = max(0.0, logistics_cost)
    buy_price = max(0.0, buy_price)
    sell_price = max(0.0, sell_price)
    volume_ton = max(0.0, volume_ton)
    exchange_rate = exchange_rate if exchange_rate > 0 else 7.2

    # 杂质仅做轻微扣减（几乎不扣钱）
    impurity_penalty = max(0.0, (sio2_grade - 3.0) * 0.15)
    actual_deal_price = max(0.0, sell_price - impurity_penalty)

    # 按用户要求：核心利润公式
    # 利润 = 卖出价 - 物流成本 - 买入价
    profit_per_ton = actual_deal_price - logistics_cost - buy_price
    total_profit = profit_per_ton * volume_ton

    break_even_quote = actual_deal_price - logistics_cost

    if caf2_grade >= 80:
        risk_level = "低风险"
        deal_probability = 0.86
        target_margin = 8.0
    elif caf2_grade >= 75:
        risk_level = "中风险"
        deal_probability = 0.65
        target_margin = 6.0
    else:
        risk_level = "高风险"
        deal_probability = 0.35
        target_margin = 4.0

    suggested_quote_high = max(0.0, break_even_quote - target_margin)
    suggested_quote_low = max(0.0, suggested_quote_high - 4.0)
    negotiation_space = max(0.0, suggested_quote_high - suggested_quote_low)

    quote_selected = buy_price
    profit_range_low = actual_deal_price - logistics_cost - suggested_quote_high
    profit_range_high = actual_deal_price - logistics_cost - suggested_quote_low

    trend_points: List[Dict[str, float]] = []
    min_quote = max(0.0, suggested_quote_low - 6.0)
    max_quote = suggested_quote_high + 6.0
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
        adj_sell = max(0.0, actual_deal_price + delta)
        sensitivity_points.append(
            {
                "scenario": f"卖出价{delta:+}USD",
                "profit_per_ton": round(adj_sell - logistics_cost - quote_selected, 2),
            }
        )

    passed_grade_gate = caf2_grade >= 75
    if profit_per_ton < 0:
        risk_hint = "当前利润为负，需提高卖出价或压低买入价/物流成本。"
    elif risk_level == "中风险":
        risk_hint = "当前为中风险区，建议加强复检并控制买入价。"
    elif risk_level == "高风险":
        risk_hint = "品位低于75%，建议谨慎采购或拒收。"
    else:
        risk_hint = "利润为正，建议在推荐买入区间内锁定采购。"

    cost_breakdown = {
        "买入成本": round(buy_price, 2),
        "物流成本": round(logistics_cost, 2),
        "杂质轻微扣减": round(impurity_penalty, 2),
    }

    result_interpretation = (
        f"按公式 单吨利润=卖出价({actual_deal_price:.2f})-物流成本({logistics_cost:.2f})-买入价({buy_price:.2f})，"
        f"结果为 {profit_per_ton:.2f} USD（约 {profit_per_ton * exchange_rate:.2f} RMB）；"
        f"总利润 {total_profit:.2f} USD（约 {total_profit * exchange_rate:.2f} RMB）。"
    )
    logic_basis = (
        "核心以买卖价差模型计算利润，SiO2仅做轻微扣减；"
        f"盈亏平衡买入价为 {break_even_quote:.2f} USD/吨，推荐买入区间 {suggested_quote_low:.2f}~{suggested_quote_high:.2f}。"
    )
    details = (
        f"卖出价修正={sell_price:.2f}-{impurity_penalty:.2f}={actual_deal_price:.2f}；"
        f"单吨利润={actual_deal_price:.2f}-{logistics_cost:.2f}-{buy_price:.2f}={profit_per_ton:.2f}。"
    )

    recommended_strategy = "按推荐区间采购并锁定物流" if profit_per_ton >= 0 else "优先降价采购或上调卖出价"
    decision_advice = (
        "建议成交：利润为正且风险可控。" if passed_grade_gate and profit_per_ton >= 0
        else "建议谨慎：先优化买入价/卖出价后再成交。"
    )
    profit_change_reason = "利润直接由卖出价、买入价和物流成本决定，三者任一变化都会线性影响单吨利润。"

    return TradeCalcResult(
        passed_grade_gate=passed_grade_gate,
        risk_level=risk_level,
        risk_hint=risk_hint,
        recommended_strategy=recommended_strategy,
        profit_change_reason=profit_change_reason,
        decision_advice=decision_advice,
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
