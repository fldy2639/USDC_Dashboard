from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from .anomaly_detector import detect_anomalies
from .llm_client import LLMClient
from .metrics_builder import build_metrics_summary
from .prompt_builder import build_prompts


def _fallback_report(metrics: dict[str, Any], anomalies: list[dict[str, Any]], error: str) -> str:
    market = metrics["market_activity"]
    target = metrics.get("target_address")
    target_text = "未提供目标地址。"
    if target:
        target_text = (
            f"目标地址净流入 {target['net_flow_usdc']:,.2f} USDC，"
            f"接收 {target['total_received_usdc']:,.2f}，发送 {target['total_sent_usdc']:,.2f}。"
        )
    anomaly_lines = "\n".join([f"- {item['message']}" for item in anomalies]) or "- 当前窗口未触发规则异常。"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "## Web3 现货运营观察日报（兜底）\n\n"
        f"生成时间：{now}\n\n"
        "### 1. 数据概览\n"
        f"- 转账条数：{market['transfer_count']}\n"
        f"- 总转账量：{market['total_volume_usdc']:,.2f} USDC\n"
        f"- 活跃地址数：{market['active_address_count']}\n\n"
        "### 2. 异常信号\n"
        f"{anomaly_lines}\n\n"
        "### 3. 目标地址分析\n"
        f"- {target_text}\n\n"
        "### 4. 运营建议\n"
        "- 重点复核 Top1 接收地址是否为交易所归集地址。\n"
        "- 结合链上后续窗口观察大额转账是否持续。\n\n"
        "### 5. 风险提示\n"
        f"- LLM 调用失败，当前报告为模板兜底。错误信息：{error}"
    )


def generate_agent_report(
    df: pd.DataFrame,
    target_address: str | None,
    whale_threshold: float,
    model_override: str | None = None,
    high_activity_threshold: int = 5000,
    top1_ratio_threshold: float = 0.30,
    target_net_flow_threshold: float = 1_000_000,
) -> dict[str, Any]:
    metrics = build_metrics_summary(
        df=df,
        target_address=target_address,
        whale_threshold=whale_threshold,
        top_n=10,
    )
    anomalies = detect_anomalies(
        df=df,
        metrics=metrics,
        whale_threshold=whale_threshold,
        high_activity_threshold=high_activity_threshold,
        top1_ratio_threshold=top1_ratio_threshold,
        target_net_flow_threshold=target_net_flow_threshold,
    )
    system_prompt, user_prompt = build_prompts(metrics=metrics, anomalies=anomalies)
    try:
        llm = LLMClient(model=model_override or None)
        report = llm.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        return {
            "report_markdown": report,
            "metrics": metrics,
            "anomalies": anomalies,
            "prompt": {"system": system_prompt, "user": user_prompt},
            "fallback_used": False,
            "error": "",
        }
    except Exception as exc:
        report = _fallback_report(metrics=metrics, anomalies=anomalies, error=str(exc))
        return {
            "report_markdown": report,
            "metrics": metrics,
            "anomalies": anomalies,
            "prompt": {"system": system_prompt, "user": user_prompt},
            "fallback_used": True,
            "error": str(exc),
        }
