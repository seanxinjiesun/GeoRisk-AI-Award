from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TradeCalcResult:
    passed_grade_gate: bool
    penalty: float
    max_buy_price: float
    details: str


def calculate_trade(caf2_grade: float, sio2_grade: float, logistics_cost: float, target_price: float) -> TradeCalcResult:
    if caf2_grade < 80:
        return TradeCalcResult(
            passed_grade_gate=False,
            penalty=0.0,
            max_buy_price=0.0,
            details=f"品位{caf2_grade:.2f}%低于80%红线，建议弃单或转低端用途。",
        )

    penalty = max(0.0, (sio2_grade - 2.0) * 2.0)
    max_buy_price = target_price - logistics_cost - penalty - 10
    details = (
        f"基准价{target_price:.2f} - 物流{logistics_cost:.2f} - 扣罚{penalty:.2f} - 杂费10.00 = 最高坑口价{max_buy_price:.2f}"
    )

    return TradeCalcResult(
        passed_grade_gate=True,
        penalty=round(penalty, 2),
        max_buy_price=round(max_buy_price, 2),
        details=details,
    )
