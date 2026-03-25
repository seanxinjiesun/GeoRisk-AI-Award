from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class ComplianceResult:
    risk_level: str
    triggers: List[str]
    summary: str


def analyze_company_risk(company_name: str, license_no: str = "") -> ComplianceResult:
    name = company_name.strip().lower()
    triggers: List[str] = []

    if len(name) < 4:
        triggers.append("企业名称信息过短，真实性检索困难")

    high_risk_words = ["agent", "broker", "consult", "middle", "中介", "壳"]
    if any(word in name for word in high_risk_words):
        triggers.append("名称包含高风险中介/壳公司特征词")

    if not license_no.strip():
        triggers.append("缺少矿权编号，合规核验不完整")

    if len(triggers) == 0:
        level = "低风险"
    elif len(triggers) == 1:
        level = "中风险"
    elif len(triggers) == 2:
        level = "高风险"
    else:
        level = "极高风险"

    summary = f"企业风险等级：{level}。触发项数量：{len(triggers)}。"
    return ComplianceResult(risk_level=level, triggers=triggers, summary=summary)
