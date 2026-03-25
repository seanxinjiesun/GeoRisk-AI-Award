from __future__ import annotations

from typing import Dict, List


def build_due_diligence_report(
    basic_info: Dict[str, str],
    company_risk_level: str,
    geology_stage: str,
    score: float,
    weighted_scores: Dict[str, float],
    decision_codes: List[str],
    final_decision: str,
    uncertainty_notes: List[str],
) -> str:
    notes_text = "\n".join(f"- {n}" for n in uncertainty_notes) if uncertainty_notes else "- 无"
    decision_codes_text = ", ".join(decision_codes) if decision_codes else "无"

    return f"""
一、项目基本信息
- 项目名称：{basic_info.get('project_name', '未提供')}
- 公司名称：{basic_info.get('company_name', '未提供')}
- 矿种：{basic_info.get('mineral_type', '未提供')}

二、企业与风险评估
- 企业风险等级：{company_risk_level}

三、地质分析
- 漏斗分级结论：{geology_stage}
- 不确定性说明：
{notes_text}

四、矿体建模
- 资源量估算公式：资源量 = 长 x 宽 x 厚 x 密度
- 资源分类术语：Speculative Target / Inferred Resource / Indicated Resource

五、项目潜力评估
- 地质潜力：{weighted_scores.get('geological_potential', 0)}
- 数据完整性：{weighted_scores.get('data_integrity', 0)}
- 项目阶段：{weighted_scores.get('project_stage', 0)}
- 风险因素：{weighted_scores.get('risk_factor', 0)}

六、Geo-Risk Score
- 总分：{score}

七、决策编号系统
- 触发编号：{decision_codes_text}

八、最终投资建议
- 结论：{final_decision}
""".strip()
