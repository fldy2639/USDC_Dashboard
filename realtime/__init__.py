"""
Week4 实时看板子包：拉取与解析主网 USDC Transfer 日志。

入口仍使用项目根目录的 `streamlit run dashboard.py`；业务代码在 `realtime` 中。
"""

from .config import (
    USDC_CONTRACT_ADDRESS,
    USDC_DECIMALS,
    USDC_TRANSFER_ABI_MIN,
    USDC_TRANSFER_TOPIC0,
)
from .fetcher import create_web3_client, fetch_usdc_transfer_logs
from .parser import create_usdc_contract, parse_usdc_transfer_logs

__all__ = [
    "USDC_CONTRACT_ADDRESS",
    "USDC_DECIMALS",
    "USDC_TRANSFER_ABI_MIN",
    "USDC_TRANSFER_TOPIC0",
    "create_usdc_contract",
    "create_web3_client",
    "fetch_usdc_transfer_logs",
    "parse_usdc_transfer_logs",
]
