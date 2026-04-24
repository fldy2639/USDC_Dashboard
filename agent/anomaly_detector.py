from __future__ import annotations

from typing import Any

import pandas as pd


def detect_anomalies(
    df: pd.DataFrame,
    metrics: dict[str, Any],
    whale_threshold: float = 1_000_000,
    high_activity_threshold: int = 5000,
    top1_ratio_threshold: float = 0.30,
    target_net_flow_threshold: float = 1_000_000,
) -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    if df.empty:
        return anomalies

    whale_rows = df[df["value_usdc"] >= whale_threshold]
    if not whale_rows.empty:
        anomalies.append(
            {
                "type": "whale_transfer",
                "level": "high",
                "message": f"检测到 {len(whale_rows)} 笔大额转账（阈值 >= {whale_threshold:,.2f} USDC）。",
                "count": int(len(whale_rows)),
            }
        )

    top_ratio = float(metrics["top_addresses"]["top1_receiver_ratio"])
    if top_ratio >= top1_ratio_threshold:
        anomalies.append(
            {
                "type": "high_concentration",
                "level": "medium",
                "message": f"Top1 接收地址占比 {top_ratio:.2%}，高于阈值 {top1_ratio_threshold:.0%}。",
                "ratio": top_ratio,
            }
        )

    transfer_count = int(metrics["market_activity"]["transfer_count"])
    if transfer_count >= high_activity_threshold:
        anomalies.append(
            {
                "type": "high_activity",
                "level": "medium",
                "message": f"当前窗口转账条数 {transfer_count}，高于阈值 {high_activity_threshold}。",
                "count": transfer_count,
            }
        )

    target_stats = metrics.get("target_address")
    if target_stats:
        net_flow = float(target_stats.get("net_flow_usdc", 0))
        if net_flow >= target_net_flow_threshold:
            anomalies.append(
                {
                    "type": "target_large_inflow",
                    "level": "high",
                    "message": f"目标地址净流入 {net_flow:,.2f} USDC，超过阈值 {target_net_flow_threshold:,.2f}。",
                    "net_flow_usdc": net_flow,
                }
            )
        elif net_flow <= -target_net_flow_threshold:
            anomalies.append(
                {
                    "type": "target_large_outflow",
                    "level": "high",
                    "message": f"目标地址净流出 {abs(net_flow):,.2f} USDC，超过阈值 {target_net_flow_threshold:,.2f}。",
                    "net_flow_usdc": net_flow,
                }
            )

    return anomalies
