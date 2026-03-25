from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.metrics_logger import compute_kpis


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
METRICS_PATH = DATA_DIR / "metrics_log.csv"
BENCHMARK_PATH = DATA_DIR / "benchmark_ground_truth.csv"
BASELINE_PATH = DATA_DIR / "manual_baseline_times.csv"


st.set_page_config(page_title="Geo-Risk 指标看板", layout="wide")
st.title("AI应用奖证据看板")
st.markdown("用于展示准确率、效率提升、稳定性与复用性指标。")

kpis = compute_kpis(str(METRICS_PATH))

c1, c2, c3, c4 = st.columns(4)
c1.metric("累计运行次数", kpis["run_count"])
c2.metric("运行成功率", f"{kpis['success_rate']}%")
c3.metric("平均准确率", f"{kpis['avg_accuracy']}%")
c4.metric("效率提升", f"{kpis['efficiency_gain_pct']}%")

st.markdown("---")

if METRICS_PATH.exists():
    df_metrics = pd.read_csv(METRICS_PATH)
else:
    df_metrics = pd.DataFrame()

if not df_metrics.empty:
    st.subheader("模块运行分布")
    fig_bar = px.histogram(df_metrics, x="module", color="is_success", barmode="group", title="各模块运行次数与成功情况")
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("各模块平均耗时（秒）")
    duration_df = df_metrics.groupby("module", as_index=False)["duration_seconds"].mean()
    fig_duration = px.bar(duration_df, x="module", y="duration_seconds", title="模块平均耗时")
    st.plotly_chart(fig_duration, use_container_width=True)

    st.subheader("明细日志")
    st.dataframe(df_metrics, use_container_width=True)
else:
    st.info("尚无运行日志数据。请先在主页面运行模块后再查看。")

st.markdown("---")

left, right = st.columns(2)

with left:
    st.subheader("Benchmark准确率样例")
    if BENCHMARK_PATH.exists():
        df_benchmark = pd.read_csv(BENCHMARK_PATH)
        avg_benchmark_acc = pd.to_numeric(df_benchmark["accuracy"], errors="coerce").mean()
        st.metric("Benchmark平均准确率", f"{avg_benchmark_acc:.2f}%")
        st.dataframe(df_benchmark, use_container_width=True)
    else:
        st.warning("未找到 benchmark_ground_truth.csv")

with right:
    st.subheader("人工 vs 系统耗时样例")
    if BASELINE_PATH.exists():
        df_baseline = pd.read_csv(BASELINE_PATH)
        manual_avg = pd.to_numeric(df_baseline["manual_minutes"], errors="coerce").mean()
        app_avg = pd.to_numeric(df_baseline["app_minutes"], errors="coerce").mean()
        gain = ((manual_avg - app_avg) / manual_avg * 100) if manual_avg else 0
        st.metric("样例效率提升", f"{gain:.2f}%")

        melt_df = df_baseline.melt(
            id_vars=["case_id"],
            value_vars=["manual_minutes", "app_minutes"],
            var_name="方式",
            value_name="分钟",
        )
        fig_eff = px.bar(melt_df, x="case_id", y="分钟", color="方式", barmode="group", title="单案例耗时对比")
        st.plotly_chart(fig_eff, use_container_width=True)
        st.dataframe(df_baseline, use_container_width=True)
    else:
        st.warning("未找到 manual_baseline_times.csv")
