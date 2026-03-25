from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd


METRICS_COLUMNS = [
    "timestamp",
    "module",
    "case_id",
    "duration_seconds",
    "is_success",
    "accuracy",
    "manual_minutes",
    "app_minutes",
]


def init_metrics_file(path: str) -> None:
    p = Path(path)
    if not p.exists():
        pd.DataFrame(columns=METRICS_COLUMNS).to_csv(p, index=False, encoding="utf-8-sig")


def log_metric(path: str, row: Dict) -> None:
    init_metrics_file(path)
    p = Path(path)
    df = pd.read_csv(p)

    complete_row = {col: row.get(col, "") for col in METRICS_COLUMNS}
    if not complete_row.get("timestamp"):
        complete_row["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.concat([df, pd.DataFrame([complete_row])], ignore_index=True)
    df.to_csv(p, index=False, encoding="utf-8-sig")


def compute_kpis(metrics_path: str) -> Dict[str, float]:
    p = Path(metrics_path)
    if not p.exists():
        return {
            "run_count": 0,
            "success_rate": 0.0,
            "avg_accuracy": 0.0,
            "efficiency_gain_pct": 0.0,
        }

    df = pd.read_csv(p)
    if df.empty:
        return {
            "run_count": 0,
            "success_rate": 0.0,
            "avg_accuracy": 0.0,
            "efficiency_gain_pct": 0.0,
        }

    run_count = len(df)
    success_rate = float((df["is_success"] == True).mean() * 100) if "is_success" in df else 0.0

    acc_series = pd.to_numeric(df.get("accuracy", pd.Series(dtype=float)), errors="coerce").dropna()
    avg_accuracy = float(acc_series.mean()) if not acc_series.empty else 0.0

    manual_series = pd.to_numeric(df.get("manual_minutes", pd.Series(dtype=float)), errors="coerce").dropna()
    app_series = pd.to_numeric(df.get("app_minutes", pd.Series(dtype=float)), errors="coerce").dropna()

    if not manual_series.empty and not app_series.empty and manual_series.mean() > 0:
        efficiency_gain = (manual_series.mean() - app_series.mean()) / manual_series.mean() * 100
    else:
        efficiency_gain = 0.0

    return {
        "run_count": run_count,
        "success_rate": round(success_rate, 2),
        "avg_accuracy": round(avg_accuracy, 2),
        "efficiency_gain_pct": round(float(efficiency_gain), 2),
    }
