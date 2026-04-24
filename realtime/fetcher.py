#!/usr/bin/env python3
"""
数据获取：实时 USDC Transfer 日志拉取（eth_getLogs 分块 + 重试/限速）。

职责：连接节点、分块拉取原始日志，不做业务解析。
"""

from __future__ import annotations

import time
from typing import Any

import requests
from web3 import Web3

from config import get_alchemy_rpc_url

from .config import USDC_CONTRACT_ADDRESS, USDC_TRANSFER_TOPIC0

# 包外引用旧路径时仍可见（与单模块时代一致）
__all__ = [
    "USDC_CONTRACT_ADDRESS",
    "USDC_TRANSFER_TOPIC0",
    "create_web3_client",
    "fetch_usdc_transfer_logs",
]


def create_web3_client() -> Web3:
    """
    创建并校验 Web3 连接。

    返回:
        Web3: 已连接的 Web3 实例。

    异常:
        ConnectionError: 无法连接节点时抛出。
    """
    rpc_url = get_alchemy_rpc_url()
    # 某些 requests/urllib3 + zstd 组合会在 keep-alive 连接上触发解压复用异常，
    # 显式限制 Accept-Encoding 并关闭连接复用，避免 zstd 解压错误。
    session = requests.Session()
    session.headers.update(
        {
            "Accept-Encoding": "gzip, deflate, identity",
            "Connection": "close",
        }
    )
    provider = Web3.HTTPProvider(
        rpc_url,
        request_kwargs={"timeout": 30},
        session=session,
    )
    w3 = Web3(provider)
    if not w3.is_connected():
        raise ConnectionError("无法连接以太坊节点，请检查 ALCHEMY_API_KEY 或网络状态。")
    return w3


def fetch_usdc_transfer_logs(
    w3: Web3,
    end_block: int,
    block_span: int,
    chunk_size: int = 10,
    sleep_seconds: float = 0.05,
    max_retries: int = 3,
    retry_backoff_seconds: float = 0.8,
) -> list[dict[str, Any]]:
    """
    分块拉取 USDC Transfer 原始日志（eth_getLogs）。

    主网 USDC 交易量极大，**同一多区块 range 的返回可能超过节点单响应限制**；本函数在“重试仍失败”时会对该区段
    **自动二分拆块**再查，故侧边栏的“分块大小”不奏效时仍可能因日志量触顶，拆分后可继续拉取（RPC 次数会增加）。

    参数:
        w3: Web3 客户端实例。
        end_block: 查询结束区块（包含）。
        block_span: 向前覆盖的区块数量（包含 end_block）。
        chunk_size: 每次请求的区块跨度，默认 10。
        sleep_seconds: 每个分块请求后的暂停秒数，默认 0.05。
        max_retries: 单分块失败时最大重试次数，默认 3。
        retry_backoff_seconds: 重试基准退避秒数，默认 0.8。

    返回:
        list[dict[str, Any]]: 原始日志列表（不做业务解析）。

    异常:
        ValueError: 参数非法时抛出。
        RuntimeError: 超过重试次数后仍失败时抛出。
    """
    if block_span <= 0:
        raise ValueError("block_span 必须大于 0。")
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0。")
    if end_block < 0:
        raise ValueError("end_block 不能为负数。")

    start_block = max(0, end_block - block_span + 1)
    checksum_contract = Web3.to_checksum_address(USDC_CONTRACT_ADDRESS)

    all_logs: list[dict[str, Any]] = []
    for chunk_start in range(start_block, end_block + 1, chunk_size):
        chunk_end = min(chunk_start + chunk_size - 1, end_block)
        all_logs.extend(
            _get_logs_with_retry_and_split(
                w3=w3,
                checksum_contract=checksum_contract,
                from_block=chunk_start,
                to_block=chunk_end,
                max_retries=max_retries,
                retry_backoff_seconds=retry_backoff_seconds,
                sleep_seconds=sleep_seconds,
            )
        )
    return all_logs


def _get_logs_with_retry_and_split(
    w3: Web3,
    checksum_contract: str,
    from_block: int,
    to_block: int,
    max_retries: int,
    retry_backoff_seconds: float,
    sleep_seconds: float,
) -> list[dict[str, Any]]:
    """
    对 [from_block, to_block] 做 get_logs，带重试；仍失败时二分区间（USDC 极活跃，多区块时易触顶节点单响应体积限制）。

    参数:
        w3: Web3 实例。
        checksum_contract: USDC 合约地址（已 checksum）。
        from_block: 起块（含）。
        to_block: 止块（含）。
        max_retries: 同 fetch_usdc_transfer_logs。
        retry_backoff_seconds: 同 fetch_usdc_transfer_logs。
        sleep_seconds: 成功后额外停顿，降速限。

    返回:
        list: 本区间内的全部日志。

    异常:
        RuntimeError: 单块在重试后仍失败时抛出，并附带节点返回原因。
    """
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            logs = w3.eth.get_logs(
                {
                    "fromBlock": from_block,
                    "toBlock": to_block,
                    "address": checksum_contract,
                    "topics": [USDC_TRANSFER_TOPIC0],
                }
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return logs
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(retry_backoff_seconds * attempt)

    # 多区块时常见：单响应内日志量过大，改为拆成更小范围
    if from_block < to_block and last_error is not None:
        mid = (from_block + to_block) // 2
        left = _get_logs_with_retry_and_split(
            w3, checksum_contract, from_block, mid, max_retries, retry_backoff_seconds, sleep_seconds
        )
        right = _get_logs_with_retry_and_split(
            w3, checksum_contract, mid + 1, to_block, max_retries, retry_backoff_seconds, sleep_seconds
        )
        return left + right

    if last_error is not None:
        raise RuntimeError(
            f"区块 {from_block} 拉取仍失败，已重试 {max_retries} 次。节点返回: {last_error!s}"
        ) from last_error
    return []
