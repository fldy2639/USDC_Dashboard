#!/usr/bin/env python3
"""
Web3 SpotOps Agent：USDC 资金流看板 + Agent 分析。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from agent import generate_agent_report
from analyzer import (
    analyze_address_activity,
    compute_daily_tx_count,
    compute_daily_volume,
    ensure_datetime,
    load_usdc_csv,
    summarize_top_addresses,
)
from realtime import USDC_CONTRACT_ADDRESS, create_web3_client, fetch_usdc_transfer_logs, parse_usdc_transfer_logs


SAMPLE_CSV_PATH = Path("data/sample_usdc_transfers.csv")


def _safe_address_filter(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    kw = keyword.strip().lower()
    if not kw:
        return df
    mask = df["from"].str.lower().str.contains(kw) | df["to"].str.lower().str.contains(kw)
    return df.loc[mask].copy()


@st.cache_data(show_spinner=False, ttl=45)
def load_realtime_data(end_block: int, block_span: int, chunk_size: int) -> pd.DataFrame:
    w3 = create_web3_client()
    raw_logs = fetch_usdc_transfer_logs(
        w3=w3,
        end_block=end_block,
        block_span=block_span,
        chunk_size=chunk_size,
    )
    if not raw_logs:
        return pd.DataFrame()
    parsed = parse_usdc_transfer_logs(
        w3=w3,
        contract_address=USDC_CONTRACT_ADDRESS,
        raw_logs=raw_logs,
    )
    return ensure_datetime(parsed)


@st.cache_data(show_spinner=False)
def load_sample_data(path: str) -> pd.DataFrame:
    return ensure_datetime(load_usdc_csv(path))


def render_overview_tab(df: pd.DataFrame, target_address: str) -> None:
    total_rows = len(df)
    total_volume = float(df["value_usdc"].sum()) if total_rows else 0.0
    active_addresses = pd.concat([df["from"], df["to"]], ignore_index=True).nunique()

    net_flow = None
    if target_address.strip():
        stats = analyze_address_activity(df, target_address.strip())
        net_flow = float(stats["net_flow_usdc"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("样本日志条数", f"{total_rows:,}")
    c2.metric("总转账量(USDC)", f"{total_volume:,.2f}")
    c3.metric("活跃地址数", f"{active_addresses:,}")
    c4.metric("目标地址净流入(USDC)", "-" if net_flow is None else f"{net_flow:,.2f}")

    top_receivers = pd.DataFrame(summarize_top_addresses(df, top_n=10)["top_receivers"])
    if not top_receivers.empty:
        fig = px.bar(top_receivers, x="address", y="amount_usdc", title="Top10 接收地址（按 USDC）")
        fig.update_layout(xaxis_title="地址", yaxis_title="USDC")
        st.plotly_chart(fig, use_container_width=True)


def render_events_tab(df: pd.DataFrame) -> None:
    address_kw = st.text_input("按地址关键词筛选（from/to）", value="", key="events_filter")
    filtered = _safe_address_filter(df, address_kw)
    st.caption(f"当前展示 {len(filtered):,} / {len(df):,} 条日志")
    st.dataframe(
        filtered[
            [
                "datetime",
                "block_number",
                "transaction_hash",
                "log_index",
                "from",
                "to",
                "value_usdc",
            ]
        ].sort_values(["block_number", "log_index"], ascending=False),
        use_container_width=True,
        height=500,
    )


def render_timeseries_tab(df: pd.DataFrame) -> None:
    daily_volume = compute_daily_volume(df)
    daily_tx = compute_daily_tx_count(df)

    if not daily_volume.empty:
        fig_volume = px.line(
            daily_volume,
            x="date",
            y="daily_volume_usdc",
            markers=True,
            title="USDC 每日转账总量",
        )
        fig_volume.update_layout(xaxis_title="日期(UTC)", yaxis_title="USDC")
        st.plotly_chart(fig_volume, use_container_width=True)

    if not daily_tx.empty:
        fig_tx = px.bar(
            daily_tx,
            x="date",
            y="daily_tx_count",
            title="USDC 每日日志条数",
        )
        fig_tx.update_layout(xaxis_title="日期(UTC)", yaxis_title="日志条数")
        st.plotly_chart(fig_tx, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.dataframe(daily_volume, use_container_width=True, height=280)
    c2.dataframe(daily_tx, use_container_width=True, height=280)


def render_address_tab(df: pd.DataFrame, target_address: str) -> None:
    address = target_address.strip()
    if not address:
        st.info("请在顶部输入目标地址后查看地址分析。")
        return

    stats = analyze_address_activity(df, address)
    c1, c2, c3 = st.columns(3)
    c1.metric("接收金额(USDC)", f"{stats['total_received_usdc']:,.2f}")
    c2.metric("发送金额(USDC)", f"{stats['total_sent_usdc']:,.2f}")
    c3.metric("净流入(USDC)", f"{stats['net_flow_usdc']:,.2f}")

    st.write("交易统计")
    st.json(
        {
            "tx_count_in": stats["tx_count_in"],
            "tx_count_out": stats["tx_count_out"],
            "tx_count_total": stats["tx_count_total"],
            "unique_txs_in": stats["unique_txs_in"],
            "unique_txs_out": stats["unique_txs_out"],
            "first_seen": stats["first_seen"],
            "last_seen": stats["last_seen"],
        }
    )

    df_addr = df[(df["from"].str.lower() == address.lower()) | (df["to"].str.lower() == address.lower())]
    st.dataframe(
        df_addr[
            ["datetime", "transaction_hash", "from", "to", "value_usdc", "block_number", "log_index"]
        ].sort_values(["block_number", "log_index"], ascending=False),
        use_container_width=True,
        height=420,
    )


def render_agent_tab(
    df: pd.DataFrame,
    data_mode: str,
    target_address: str,
    whale_threshold: float,
    llm_model: str,
) -> None:
    st.write("### AI Agent 分析")
    st.caption(
        f"当前窗口：{df['datetime'].min()} 到 {df['datetime'].max()}，数据模式：{data_mode}，日志条数：{len(df):,}"
    )
    run_agent = st.button("生成 AI 分析报告", type="primary")
    if run_agent:
        with st.spinner("正在生成 Agent 报告..."):
            result = generate_agent_report(
                df=df,
                target_address=target_address,
                whale_threshold=whale_threshold,
                model_override=llm_model or None,
            )
        st.session_state["agent_result"] = result

    result = st.session_state.get("agent_result")
    if not result:
        st.info("点击“生成 AI 分析报告”后查看结果。")
        return

    if result["fallback_used"]:
        st.warning(f"LLM 调用失败，已使用兜底模板。错误：{result['error']}")

    st.markdown(result["report_markdown"])
    st.download_button(
        "下载 Markdown 报告",
        data=result["report_markdown"],
        file_name="spotops_agent_report.md",
        mime="text/markdown",
    )
    st.code(result["report_markdown"], language="markdown")

    with st.expander("Agent 输入指标 JSON（调试）", expanded=False):
        st.json(result["metrics"])
    with st.expander("规则异常 JSON（调试）", expanded=False):
        st.json(result["anomalies"])
    with st.expander("Prompt 预览（调试）", expanded=False):
        st.text(result["prompt"]["system"])
        st.text(result["prompt"]["user"][:4000])


def main() -> None:
    st.set_page_config(page_title="Web3 SpotOps Agent", layout="wide")
    st.title("Web3 SpotOps Agent：USDC 鲸鱼资金流监控与 AI 分析助手")
    st.caption("数据流：fetcher/parser -> analyzer -> anomaly detector -> LLM agent -> dashboard")

    latest_block: int | None = None
    with st.sidebar:
        st.subheader("查询参数")
        data_mode = st.selectbox("数据模式", options=["实时数据", "示例数据"], index=0)
        target_address = st.text_input("目标地址（可选）", value="")
        whale_threshold = st.number_input(
            "大额转账阈值(USDC)", min_value=1_000.0, max_value=100_000_000.0, value=1_000_000.0, step=100_000.0
        )
        llm_model = st.text_input("LLM 模型名称", value="deepseek-v4-flash")
        block_span = st.number_input("覆盖区块数", min_value=20, max_value=5000, value=200, step=20)
        chunk_size = st.number_input("分块查询大小", min_value=5, max_value=200, value=10, step=5)
        end_block = 0
        if data_mode == "实时数据":
            try:
                w3 = create_web3_client()
                latest_block = int(w3.eth.block_number)
            except Exception as exc:
                st.error(f"节点连接失败：{exc}")
                st.stop()
            end_block = int(
                st.number_input(
                    "结束区块",
                    min_value=max(0, latest_block - 10_000),
                    max_value=latest_block,
                    value=latest_block,
                    step=1,
                )
            )
            st.write(f"当前最新区块：{latest_block:,}")
        else:
            st.write(f"示例数据文件：{SAMPLE_CSV_PATH}")
        if st.button("刷新数据", type="primary"):
            load_realtime_data.clear()
            load_sample_data.clear()
            st.session_state.pop("agent_result", None)

    if data_mode == "实时数据":
        with st.spinner("正在拉取并解析实时 USDC 日志..."):
            df = load_realtime_data(end_block=int(end_block), block_span=int(block_span), chunk_size=int(chunk_size))
    else:
        try:
            df = load_sample_data(str(SAMPLE_CSV_PATH))
        except Exception as exc:
            st.error(f"示例数据加载失败：{exc}")
            st.stop()

    if df.empty:
        st.warning("未获取到日志，请调整参数后重试。")
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["概览", "事件流", "时间序列", "地址分析", "AI Agent 分析"])
    with tab1:
        render_overview_tab(df, target_address)
    with tab2:
        render_events_tab(df)
    with tab3:
        render_timeseries_tab(df)
    with tab4:
        render_address_tab(df, target_address)
    with tab5:
        render_agent_tab(
            df=df,
            data_mode=data_mode,
            target_address=target_address,
            whale_threshold=float(whale_threshold),
            llm_model=llm_model.strip(),
        )


if __name__ == "__main__":
    main()
