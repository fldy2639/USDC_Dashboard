#!/usr/bin/env python3
"""
数据解析：将原始 USDC Transfer 日志解析为与 Week2/Week3 对齐的 DataFrame。
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from web3 import Web3

from .config import USDC_DECIMALS, USDC_TRANSFER_ABI_MIN


def create_usdc_contract(w3: Web3, contract_address: str):
    """
    创建 USDC 合约对象（仅用于 process_log 解析日志）。

    参数:
        w3: Web3 客户端实例。
        contract_address: USDC 合约地址。

    返回:
        Contract: 可用于 process_log 的合约对象。
    """
    return w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=USDC_TRANSFER_ABI_MIN,
    )


def _extract_timestamp_from_raw_log(raw_log: dict[str, Any]) -> int | None:
    """
    尝试从原始日志提取时间戳（不同节点格式兼容）。

    参数:
        raw_log: 原始日志对象。

    返回:
        int | None: 秒级时间戳；若不存在则返回 None。
    """
    block_ts = raw_log.get("blockTimestamp")
    if block_ts is None:
        return None
    if isinstance(block_ts, str):
        return int(block_ts, 16) if block_ts.startswith("0x") else int(block_ts)
    return int(block_ts)


def parse_usdc_transfer_logs(
    w3: Web3,
    contract_address: str,
    raw_logs: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    将 USDC Transfer 原始日志解析为标准化 DataFrame。

    参数:
        w3: Web3 客户端实例。
        contract_address: USDC 合约地址。
        raw_logs: fetcher 拉取的原始日志列表。

    返回:
        pd.DataFrame: 标准字段表，列与 Week2/Week3 对齐。
    """
    contract = create_usdc_contract(w3, contract_address)
    block_ts_cache: dict[int, int] = {}
    parsed_rows: list[dict[str, Any]] = []

    def _get_block_timestamp(block_number: int) -> int:
        """
        获取区块时间戳并缓存，减少重复 RPC。

        参数:
            block_number: 区块高度。

        返回:
            int: 秒级时间戳。
        """
        if block_number in block_ts_cache:
            return block_ts_cache[block_number]
        ts = int(w3.eth.get_block(block_number)["timestamp"])
        block_ts_cache[block_number] = ts
        return ts

    for raw_log in raw_logs:
        parsed_log = contract.events.Transfer().process_log(raw_log)
        args = parsed_log["args"]

        block_number = int(parsed_log["blockNumber"])
        log_index = int(parsed_log["logIndex"])
        tx_hash = parsed_log["transactionHash"].hex()
        if not tx_hash.startswith("0x"):
            tx_hash = f"0x{tx_hash}"

        value_raw = int(args["value"])
        value_usdc = value_raw / (10**USDC_DECIMALS)

        ts = _extract_timestamp_from_raw_log(raw_log)
        if ts is None:
            ts = _get_block_timestamp(block_number)

        parsed_rows.append(
            {
                "transaction_hash": tx_hash,
                "block_number": block_number,
                "log_index": log_index,
                "from": args["from"],
                "to": args["to"],
                "value_raw": value_raw,
                "value_usdc": value_usdc,
                "timestamp": ts,
                "datetime": pd.to_datetime(ts, unit="s", utc=True),
            }
        )

    return pd.DataFrame(parsed_rows)
