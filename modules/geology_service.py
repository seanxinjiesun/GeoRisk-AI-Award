from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pdfplumber
import pytesseract
from docx import Document
from PIL import Image

from modules.claude_client import call_claude


MINING_KEYWORDS = [
    "caf2",
    "sio2",
    "ore",
    "deposit",
    "grade",
    "矿",
    "矿体",
    "品位",
    "成矿",
    "钻孔",
    "萤石",
]


@dataclass
class FileAIResult:
    mode: str  # mining | general
    summary: str
    key_insights: List[str]
    bullet_points: List[str]
    risk_issues: str
    application_advice: str

    mineral_type: str
    grade_info: str
    deposit_type: str
    orebody_scale: str
    thickness_extension: str
    mineability: str

    geological_info: str
    orebody_analysis: str
    data_integrity: str
    risk_identification: str
    investment_advice: str

    result_interpretation: str
    logic_basis: str
    risk_hint: str
    risk_level: str
    radar_scores: Dict[str, float]
    highlight_keywords: List[str]
    raw_response: str
    runtime_mode: str  # online | demo
    is_demo_data: bool
    demo_notice: str


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf_with_pdfplumber(path: Path) -> str:
    parts: List[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _ocr_pdf_with_pytesseract(path: Path) -> str:
    try:
        import pypdfium2 as pdfium
    except Exception:
        return ""

    ocr_parts: List[str] = []
    try:
        pdf = pdfium.PdfDocument(str(path))
        for i in range(len(pdf)):
            page = pdf.get_page(i)
            bitmap = page.render(scale=2)
            pil_img = bitmap.to_pil()
            ocr_parts.append(pytesseract.image_to_string(pil_img, lang="eng+chi_sim"))
            page.close()
    except Exception:
        return ""

    return "\n".join(ocr_parts)


def _read_image_with_ocr(path: Path) -> str:
    try:
        img = Image.open(str(path))
        return pytesseract.image_to_string(img, lang="eng+chi_sim")
    except Exception:
        return ""


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return _read_txt(path)
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        text = _read_pdf_with_pdfplumber(path)
        if len(text.strip()) < 120:
            text = f"{text}\n{_ocr_pdf_with_pytesseract(path)}".strip()
        return text
    if suffix in {".png", ".jpg", ".jpeg", ".bmp"}:
        return _read_image_with_ocr(path)

    raise ValueError("仅支持 .txt/.docx/.pdf/.png/.jpg/.jpeg/.bmp 文件")


def _is_mining_related(report_text: str) -> bool:
    lower = report_text.lower()
    return any(k in lower for k in MINING_KEYWORDS)


def _build_prompt(mode: str, company_name: str, project_name: str, report_text: str) -> str:
    clipped = report_text[:12000]
    if mode == "mining":
        return f"""
你是矿业投资与地质尽调专家。请输出严格JSON，不要输出JSON外文本。

公司名称：{company_name or '未提供'}
项目名称：{project_name or '未提供'}
文档内容：
{clipped}

输出JSON：
{{
  "summary": "整体结论摘要",
  "mineral_type": "矿种判断",
  "grade_info": "品位信息（如CaF2、SiO2）",
  "deposit_type": "成矿类型",
  "orebody_scale": "矿体规模",
  "thickness_extension": "厚度与延伸",
  "mineability": "可采性评估",
  "geological_info": "地质信息识别综合结论",
  "orebody_analysis": "矿体信息分析综合结论",
  "data_integrity": "数据完整性（是否具备决策所需信息、是否缺关键数据）",
  "risk_identification": "风险识别（地质风险/开采风险/合规风险）",
  "investment_advice": "建议继续/谨慎/放弃（三选一）",
  "result_interpretation": "结果说明",
  "logic_basis": "逻辑依据",
  "risk_hint": "风险提示",
  "risk_level": "低风险/中风险/高风险",
  "radar_scores": {{
    "geological_potential": 0-100,
    "data_integrity": 0-100,
    "project_stage": 0-100,
    "risk_factor": 0-100
  }},
  "highlight_keywords": ["矿种", "CaF2", "SiO2"]
}}
""".strip()

    return f"""
你是企业文档分析顾问。请输出严格JSON，不要输出JSON外文本。

公司名称：{company_name or '未提供'}
项目名称：{project_name or '未提供'}
文档内容：
{clipped}

输出JSON：
{{
  "summary": "文件摘要",
  "key_insights": ["关键信息1", "关键信息2", "关键信息3"],
  "bullet_points": ["结构化要点1", "结构化要点2", "结构化要点3"],
  "risk_issues": "风险/问题识别（若无则写未发现显著风险）",
  "application_advice": "应用建议（是否值得参考）",
  "result_interpretation": "结果说明",
  "logic_basis": "逻辑依据",
  "risk_hint": "风险提示",
  "risk_level": "低风险/中风险/高风险",
  "highlight_keywords": ["关键词1", "关键词2", "关键词3"]
}}
""".strip()


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("未识别到JSON结构")
    return json.loads(match.group(0))


def _to_list(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _safe_scores(payload: dict) -> Dict[str, float]:
    radar = payload.get("radar_scores", {}) or {}

    def _num(v: object, default: float) -> float:
        try:
            return float(v)
        except Exception:
            return default

    return {
        "geological_potential": max(0, min(100, _num(radar.get("geological_potential"), 60))),
        "data_integrity": max(0, min(100, _num(radar.get("data_integrity"), 55))),
        "project_stage": max(0, min(100, _num(radar.get("project_stage"), 50))),
        "risk_factor": max(0, min(100, _num(radar.get("risk_factor"), 55))),
    }


def _mining_payload_fallback() -> dict:
    return {
        "summary": "文档疑似矿业相关，但结构化结果异常，建议补充数据重试。",
        "mineral_type": "未稳定识别",
        "grade_info": "未稳定识别",
        "deposit_type": "未稳定识别",
        "orebody_scale": "资料不足",
        "thickness_extension": "资料不足",
        "mineability": "谨慎评估",
        "geological_info": "地质要素可部分识别，但证据链不足。",
        "orebody_analysis": "矿体规模与稳定性信息不足。",
        "data_integrity": "关键字段缺失，建议补充钻孔与化验数据。",
        "risk_identification": "地质/开采/合规风险信息不完整。",
        "investment_advice": "谨慎",
        "result_interpretation": "仅供初筛参考，暂不建议直接投资决策。",
        "logic_basis": "AI输出异常回退保守策略。",
        "risk_hint": "优先补齐矿体连续性与品位样本数据。",
        "risk_level": "中风险",
        "highlight_keywords": ["矿体", "品位", "风险"],
        "radar_scores": {
            "geological_potential": 55,
            "data_integrity": 50,
            "project_stage": 50,
            "risk_factor": 50,
        },
    }


def _mining_payload_demo() -> dict:
    return {
        "summary": "当前为演示模式，系统基于样例矿业数据生成结构化尽调结论。",
        "mineral_type": "萤石矿（演示）",
        "grade_info": "CaF2约82%，SiO2约4.5%（演示样例）",
        "deposit_type": "热液型（演示）",
        "orebody_scale": "中型矿体（演示）",
        "thickness_extension": "厚度与延伸连续性中等（演示）",
        "mineability": "具备开发潜力，建议补充钻孔验证。",
        "geological_info": "地层与构造条件具备一定成矿指示，但证据链仍需补强。",
        "orebody_analysis": "矿体连续性尚可，局部变化较大，建议分区评估。",
        "data_integrity": "当前仅用于演示，正式决策需补齐化验与工程验证数据。",
        "risk_identification": "政策合规、品位波动与开采成本是主要风险项。",
        "investment_advice": "谨慎",
        "result_interpretation": "演示输出显示项目可作为初筛对象，不可直接替代正式尽调结论。",
        "logic_basis": "演示样例基于规则与历史结构化模板生成。",
        "risk_hint": "当前为演示数据，正式使用前请开启在线AI并补充原始地质证据。",
        "risk_level": "中风险",
        "highlight_keywords": ["演示", "CaF2", "风险"],
        "radar_scores": {
            "geological_potential": 68,
            "data_integrity": 52,
            "project_stage": 58,
            "risk_factor": 57,
        },
    }


def _general_payload_fallback() -> dict:
    return {
        "summary": "文档为通用内容，已输出摘要与建议。",
        "key_insights": ["可提取核心信息", "可用于初步决策支持"],
        "bullet_points": ["建议人工复核关键结论"],
        "risk_issues": "未发现高等级风险。",
        "application_advice": "建议结合业务场景继续使用。",
        "result_interpretation": "适合用于初筛。",
        "logic_basis": "基于文本语义与关键句提取。",
        "risk_hint": "高影响决策前建议二次复核。",
        "risk_level": "低风险",
        "highlight_keywords": ["摘要", "要点", "建议"],
    }


def _general_payload_demo() -> dict:
    return {
        "summary": "当前为演示模式，系统基于样例文档生成摘要和结构化要点。",
        "key_insights": ["演示数据用于流程展示", "关键字段可稳定输出", "支持后续人工复核"],
        "bullet_points": ["当前为演示数据", "正式评审请启用在线AI", "高影响结论建议二次校验"],
        "risk_issues": "演示模式下不判定真实业务风险等级，仅供展示流程。",
        "application_advice": "可用于路演与评委演示，正式业务请切换在线AI模式。",
        "result_interpretation": "系统功能完整可运行，结果为演示样例。",
        "logic_basis": "演示模式采用本地模板输出，避免外部API依赖。",
        "risk_hint": "当前为演示数据。",
        "risk_level": "低风险",
        "highlight_keywords": ["演示", "摘要", "结构化"],
    }


def analyze_file_with_ai(report_text: str, company_name: str = "", project_name: str = "", ai_enabled: bool = True) -> FileAIResult:
    if not report_text.strip():
        raise ValueError("文本为空，无法分析")

    mode = "mining" if _is_mining_related(report_text) else "general"
    runtime_mode = "online"
    raw = ""
    payload: dict = {}

    if ai_enabled:
        try:
            raw = call_claude(_build_prompt(mode, company_name, project_name, report_text))
            try:
                payload = _extract_json(raw)
            except Exception:
                payload = {}
        except Exception:
            runtime_mode = "demo"
            payload = {}
    else:
        runtime_mode = "demo"

    if mode == "mining":
        if runtime_mode == "demo":
            payload = _mining_payload_demo()
        elif not payload:
            payload = _mining_payload_fallback()

        advice_raw = str(payload.get("investment_advice", "谨慎"))
        if "继续" in advice_raw or "建议投资" in advice_raw:
            advice = "建议继续"
        elif "放弃" in advice_raw:
            advice = "放弃"
        else:
            advice = "谨慎"

        return FileAIResult(
            mode="mining",
            summary=str(payload.get("summary", "")),
            key_insights=[],
            bullet_points=[],
            risk_issues="",
            application_advice="",
            mineral_type=str(payload.get("mineral_type", "")),
            grade_info=str(payload.get("grade_info", "")),
            deposit_type=str(payload.get("deposit_type", "")),
            orebody_scale=str(payload.get("orebody_scale", "")),
            thickness_extension=str(payload.get("thickness_extension", "")),
            mineability=str(payload.get("mineability", "")),
            geological_info=str(payload.get("geological_info", "")),
            orebody_analysis=str(payload.get("orebody_analysis", "")),
            data_integrity=str(payload.get("data_integrity", "")),
            risk_identification=str(payload.get("risk_identification", "")),
            investment_advice=advice,
            result_interpretation=str(payload.get("result_interpretation", "")),
            logic_basis=str(payload.get("logic_basis", "")),
            risk_hint=str(payload.get("risk_hint", "")),
            risk_level=str(payload.get("risk_level", "中风险")),
            radar_scores=_safe_scores(payload),
            highlight_keywords=_to_list(payload.get("highlight_keywords")),
            raw_response=raw,
            runtime_mode=runtime_mode,
            is_demo_data=runtime_mode == "demo",
            demo_notice="当前为演示数据" if runtime_mode == "demo" else "",
        )

    if runtime_mode == "demo":
        payload = _general_payload_demo()
    elif not payload:
        payload = _general_payload_fallback()

    return FileAIResult(
        mode="general",
        summary=str(payload.get("summary", "")),
        key_insights=_to_list(payload.get("key_insights")),
        bullet_points=_to_list(payload.get("bullet_points")),
        risk_issues=str(payload.get("risk_issues", "")),
        application_advice=str(payload.get("application_advice", "")),
        mineral_type="",
        grade_info="",
        deposit_type="",
        orebody_scale="",
        thickness_extension="",
        mineability="",
        geological_info="",
        orebody_analysis="",
        data_integrity="",
        risk_identification="",
        investment_advice="",
        result_interpretation=str(payload.get("result_interpretation", "")),
        logic_basis=str(payload.get("logic_basis", "")),
        risk_hint=str(payload.get("risk_hint", "")),
        risk_level=str(payload.get("risk_level", "低风险")),
        radar_scores={"geological_potential": 0, "data_integrity": 0, "project_stage": 0, "risk_factor": 0},
        highlight_keywords=_to_list(payload.get("highlight_keywords")),
        raw_response=raw,
        runtime_mode=runtime_mode,
        is_demo_data=runtime_mode == "demo",
        demo_notice="当前为演示数据" if runtime_mode == "demo" else "",
    )
