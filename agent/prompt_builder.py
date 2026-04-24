from __future__ import annotations

import json
from typing import Any


def build_prompts(metrics: dict[str, Any], anomalies: list[dict[str, Any]]) -> tuple[str, str]:
    system_prompt = (
        "你是一个 Web3 现货平台运营分析 Agent。"
        "你必须严格基于输入指标与异常信号给出分析，不得编造数据。"
        "不要给出投资建议、价格预测或交易建议。"
    )
    user_prompt = (
        "请输出以下结构：\n"
        "1. 数据概览\n"
        "2. 主要发现\n"
        "3. 异常信号\n"
        "4. 目标地址分析\n"
        "5. 可能原因\n"
        "6. 运营建议\n"
        "7. 今日待办\n"
        "8. 风险提示\n\n"
        f"输入指标：\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n"
        f"异常信号：\n{json.dumps(anomalies, ensure_ascii=False, indent=2)}"
    )
    return system_prompt, user_prompt
