from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from docx import Document
from pypdf import PdfReader


KEYWORDS = {
    "outcrop": ["露头", "outcrop"],
    "geophysics": ["物探", "geophysics", "ip", "激电"],
    "drilling": ["钻孔", "drilling", "drill"],
    "systematic_sampling": ["系统采样", "systematic sampling"],
}


@dataclass
class GeologyParseResult:
    parsed_text: str
    flags: Dict[str, bool]
    uncertainty_notes: List[str]
    recommended_stage: str


def _read_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_docx(path: Path) -> str:
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return _read_txt(path)
    if suffix == ".docx":
        return _read_docx(path)
    if suffix == ".pdf":
        return _read_pdf(path)

    raise ValueError("仅支持 .txt/.docx/.pdf 文件")


def analyze_geology_text(text: str) -> GeologyParseResult:
    lower_text = text.lower()

    flags = {
        "has_outcrop": any(k in lower_text for k in KEYWORDS["outcrop"]),
        "has_geophysics": any(k in lower_text for k in KEYWORDS["geophysics"]),
        "has_drilling": any(k in lower_text for k in KEYWORDS["drilling"]),
        "has_systematic_sampling": any(k in lower_text for k in KEYWORDS["systematic_sampling"]),
    }

    notes: List[str] = []
    if not flags["has_outcrop"]:
        notes.append("无露头证据：项目等级需降级")
    if not flags["has_geophysics"]:
        notes.append("无物探证据：项目等级需降级")
    if not flags["has_drilling"]:
        notes.append("无钻孔数据：判定为盲矿")
    if not flags["has_systematic_sampling"]:
        notes.append("非系统采样或未说明：数据可信度不足")

    if not flags["has_drilling"]:
        stage = "三级盲矿（建议放弃）"
    elif not flags["has_geophysics"] or not flags["has_outcrop"]:
        stage = "二级观察（需补数据）"
    else:
        stage = "一级优先（具备勘探价值）"

    return GeologyParseResult(
        parsed_text=text[:3000],
        flags=flags,
        uncertainty_notes=notes,
        recommended_stage=stage,
    )
