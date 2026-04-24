#!/usr/bin/env python3
"""
USDC 主网与 Transfer 相关常量（实时看板与解析唯一配置源）。
"""

from __future__ import annotations

# USDC 主网合约
USDC_CONTRACT_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
# Transfer(address,address,uint256) 的 topic0
USDC_TRANSFER_TOPIC0 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
# 精度
USDC_DECIMALS = 6
# 简化 ABI：仅 Transfer
USDC_TRANSFER_ABI_MIN: list[dict] = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]
