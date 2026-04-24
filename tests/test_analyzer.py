#!/usr/bin/env python3
"""
analyzer 模块单元测试
"""

import pandas as pd
import pytest

from analyzer import (
    analyze_address_activity,
    compute_daily_tx_count,
    compute_daily_volume,
    ensure_datetime,
)


def _sample_df() -> pd.DataFrame:
    rows = [
        {
            "transaction_hash": "0xaa",
            "block_number": 1,
            "log_index": 0,
            "from": "0x0000000000000000000000000000000000000001",
            "to": "0x0000000000000000000000000000000000000002",
            "value_raw": 1_000_000,
            "value_usdc": 1.0,
            "timestamp": 0,
            "datetime": "1970-01-01 00:00:00+00:00",
        },
        {
            "transaction_hash": "0xbb",
            "block_number": 2,
            "log_index": 0,
            "from": "0x0000000000000000000000000000000000000002",
            "to": "0x0000000000000000000000000000000000000001",
            "value_raw": 2_000_000,
            "value_usdc": 2.0,
            "timestamp": 0,
            "datetime": "1970-01-01 12:00:00+00:00",
        },
    ]
    return pd.DataFrame(rows)


def test_daily_volume_and_tx_count():
    df = ensure_datetime(_sample_df())
    vol = compute_daily_volume(df)
    tx = compute_daily_tx_count(df)

    assert len(vol) == 1
    assert vol["daily_volume_usdc"].iloc[0] == pytest.approx(3.0)
    assert len(tx) == 1
    assert tx["daily_tx_count"].iloc[0] == 2


def test_address_activity_net_flow():
    df = ensure_datetime(_sample_df())
    addr = "0x0000000000000000000000000000000000000001"
    stats = analyze_address_activity(df, addr)

    assert stats["tx_count_in"] == 1
    assert stats["tx_count_out"] == 1
    assert stats["total_received_usdc"] == pytest.approx(2.0)
    assert stats["total_sent_usdc"] == pytest.approx(1.0)
    assert stats["net_flow_usdc"] == pytest.approx(1.0)


def test_missing_columns_raises():
    bad = pd.DataFrame({"from": [], "to": []})
    with pytest.raises(ValueError):
        ensure_datetime(bad)
