from __future__ import annotations

from pathlib import Path
import pandas as pd


def export_report_text(report_text: str, output_dir: str, filename: str = "due_diligence_report.txt") -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(report_text, encoding="utf-8")
    return str(out_path)


def export_score_detail(score_dict: dict, output_dir: str, filename: str = "score_detail.csv") -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    pd.DataFrame([score_dict]).to_csv(out_path, index=False, encoding="utf-8-sig")
    return str(out_path)
