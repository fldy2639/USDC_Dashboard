from __future__ import annotations

from typing import Any

import pandas as pd

from analyzer import analyze_address_activity, summarize_top_addresses


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_metrics_summary(
    df: pd.DataFrame,
    target_address: str | None = None,
    whale_threshold: float = 1_000_000,
    top_n: int = 10,
) -> dict[str, Any]:
    if df.empty:
        return {
            "window": {"start_time": None, "end_time": None, "block_count": 0},
            "market_activity": {
                "transfer_count": 0,
                "total_volume_usdc": 0.0,
                "active_address_count": 0,
                "avg_transfer_usdc": 0.0,
                "max_transfer_usdc": 0.0,
                "whale_transfer_count": 0,
                "whale_threshold_usdc": _to_float(whale_threshold),
            },
            "target_address": None,
            "top_addresses": {
                "top_receivers": [],
                "top_senders": [],
                "top1_receiver_ratio": 0.0,
                "top10_receiver_ratio": 0.0,
            },
        }

    transfer_count = int(len(df))
    total_volume = _to_float(df["value_usdc"].sum())
    avg_volume = _to_float(df["value_usdc"].mean()) if transfer_count else 0.0
    max_volume = _to_float(df["value_usdc"].max()) if transfer_count else 0.0
    active_addresses = int(pd.concat([df["from"], df["to"]], ignore_index=True).nunique())
    whale_count = int((df["value_usdc"] >= whale_threshold).sum())

    top_summary = summarize_top_addresses(df, top_n=top_n)
    target_stats = None
    if target_address and target_address.strip():
        target_stats = analyze_address_activity(df, target_address.strip())

    return {
        "window": {
            "start_time": str(df["datetime"].min()),
            "end_time": str(df["datetime"].max()),
            "block_count": int(df["block_number"].nunique()),
        },
        "market_activity": {
            "transfer_count": transfer_count,
            "total_volume_usdc": total_volume,
            "active_address_count": active_addresses,
            "avg_transfer_usdc": avg_volume,
            "max_transfer_usdc": max_volume,
            "whale_transfer_count": whale_count,
            "whale_threshold_usdc": _to_float(whale_threshold),
        },
        "target_address": target_stats,
        "top_addresses": {
            "top_receivers": top_summary["top_receivers"],
            "top_senders": top_summary["top_senders"],
            "top1_receiver_ratio": _to_float(top_summary["top1_receiver_ratio"]),
            "top10_receiver_ratio": _to_float(top_summary["topn_receiver_ratio"]),
        },
    }
