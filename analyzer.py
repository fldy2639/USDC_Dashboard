#!/usr/bin/env python3
"""
分析模块：提供 Pandas 聚合分析函数。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

REQUIRED_COLUMNS = {
    "transaction_hash",
    "block_number",
    "log_index",
    "from",
    "to",
    "value_raw",
    "value_usdc",
    "timestamp",
    "datetime",
}


def load_usdc_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")
    return pd.read_csv(csv_path)


def ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"缺少必要列: {sorted(missing)}")

    out = df.copy()
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce", utc=True)
    if out["datetime"].isna().all():
        out["datetime"] = pd.to_datetime(out["timestamp"], unit="s", utc=True, errors="coerce")

    if out["datetime"].isna().any():
        bad_count = int(out["datetime"].isna().sum())
        raise ValueError(f"存在无法解析的时间数据，条数: {bad_count}")

    out["date"] = out["datetime"].dt.date
    out["value_usdc"] = pd.to_numeric(out["value_usdc"], errors="coerce")
    if out["value_usdc"].isna().any():
        bad_count = int(out["value_usdc"].isna().sum())
        raise ValueError(f"存在无法解析的 value_usdc 数据，条数: {bad_count}")
    return out


def compute_daily_volume(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("date", as_index=False)["value_usdc"]
        .sum()
        .rename(columns={"value_usdc": "daily_volume_usdc"})
        .sort_values("date")
    )


def compute_daily_tx_count(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "daily_tx_count"})
        .sort_values("date")
    )


def analyze_address_activity(df: pd.DataFrame, address: str) -> dict[str, Any]:
    addr = address.lower()
    incoming = df[df["to"].str.lower() == addr].copy()
    outgoing = df[df["from"].str.lower() == addr].copy()

    total_received = float(incoming["value_usdc"].sum()) if not incoming.empty else 0.0
    total_sent = float(outgoing["value_usdc"].sum()) if not outgoing.empty else 0.0
    mask = (df["to"].str.lower() == addr) | (df["from"].str.lower() == addr)
    involved = df.loc[mask]
    if not involved.empty:
        first_seen = str(involved["datetime"].min())
        last_seen = str(involved["datetime"].max())
    else:
        first_seen = None
        last_seen = None

    return {
        "address": address,
        "tx_count_in": int(len(incoming)),
        "tx_count_out": int(len(outgoing)),
        "tx_count_total": int(len(incoming) + len(outgoing)),
        "unique_txs_in": int(incoming["transaction_hash"].nunique()) if not incoming.empty else 0,
        "unique_txs_out": int(outgoing["transaction_hash"].nunique()) if not outgoing.empty else 0,
        "total_received_usdc": total_received,
        "total_sent_usdc": total_sent,
        "net_flow_usdc": total_received - total_sent,
        "first_seen": first_seen,
        "last_seen": last_seen,
    }


def summarize_top_addresses(df: pd.DataFrame, top_n: int = 10) -> dict[str, Any]:
    """
    汇总 Top 接收/发送地址与集中度。
    """
    safe_top_n = max(1, int(top_n))
    total_volume = float(df["value_usdc"].sum()) if not df.empty else 0.0

    top_receivers_df = (
        df.groupby("to", as_index=False)["value_usdc"]
        .sum()
        .rename(columns={"to": "address", "value_usdc": "amount_usdc"})
        .sort_values("amount_usdc", ascending=False)
        .head(safe_top_n)
    )
    top_senders_df = (
        df.groupby("from", as_index=False)["value_usdc"]
        .sum()
        .rename(columns={"from": "address", "value_usdc": "amount_usdc"})
        .sort_values("amount_usdc", ascending=False)
        .head(safe_top_n)
    )

    top1_ratio = 0.0
    topn_ratio = 0.0
    if total_volume > 0 and not top_receivers_df.empty:
        top1_ratio = float(top_receivers_df.iloc[0]["amount_usdc"]) / total_volume
        topn_ratio = float(top_receivers_df["amount_usdc"].sum()) / total_volume

    return {
        "top_receivers": top_receivers_df.to_dict(orient="records"),
        "top_senders": top_senders_df.to_dict(orient="records"),
        "top1_receiver_ratio": top1_ratio,
        "topn_receiver_ratio": topn_ratio,
    }


def export_analysis_outputs(
    daily_volume_df: pd.DataFrame,
    daily_tx_count_df: pd.DataFrame,
    address_stats: Optional[dict[str, Any]],
    output_dir: str | Path,
) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    volume_path = out_dir / f"daily_volume_{ts}.csv"
    tx_count_path = out_dir / f"daily_tx_count_{ts}.csv"
    stats_path = out_dir / f"address_stats_{ts}.json"

    daily_volume_df.to_csv(volume_path, index=False)
    daily_tx_count_df.to_csv(tx_count_path, index=False)
    payload = address_stats if address_stats is not None else {}
    stats_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "daily_volume_csv": str(volume_path),
        "daily_tx_count_csv": str(tx_count_path),
        "address_stats_json": str(stats_path),
    }
