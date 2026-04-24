#!/usr/bin/env python3
"""
parser 模块单元测试
"""

from __future__ import annotations

import pandas as pd

import realtime.parser as parser_module


class _FakeTransferEvent:
    @staticmethod
    def process_log(raw_log):
        return {
            "args": {
                "from": raw_log["mock_from"],
                "to": raw_log["mock_to"],
                "value": raw_log["mock_value"],
            },
            "blockNumber": raw_log["blockNumber"],
            "transactionHash": raw_log["transactionHash"],
            "logIndex": raw_log["logIndex"],
        }


class _FakeEvents:
    @staticmethod
    def Transfer():
        return _FakeTransferEvent()


class _FakeContract:
    events = _FakeEvents()


class _FakeTxHash:
    def __init__(self, value: str):
        self._value = value

    def hex(self):
        return self._value


class _FakeEth:
    @staticmethod
    def get_block(block_number: int):
        if block_number == 100:
            return {"timestamp": 1_700_000_000}
        return {"timestamp": 1_700_000_100}


class _FakeWeb3:
    eth = _FakeEth()


def test_parse_usdc_transfer_logs_basic(monkeypatch):
    monkeypatch.setattr(parser_module, "create_usdc_contract", lambda w3, contract_address: _FakeContract())
    raw_logs = [
        {
            "blockNumber": 100,
            "transactionHash": _FakeTxHash("0xabc"),
            "logIndex": 0,
            "mock_from": "0x0000000000000000000000000000000000000001",
            "mock_to": "0x0000000000000000000000000000000000000002",
            "mock_value": 1_500_000,
            "blockTimestamp": "0x6553f100",
        }
    ]

    df = parser_module.parse_usdc_transfer_logs(
        w3=_FakeWeb3(),
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        raw_logs=raw_logs,
    )

    assert len(df) == 1
    assert df.loc[0, "transaction_hash"] == "0xabc"
    assert df.loc[0, "value_raw"] == 1_500_000
    assert df.loc[0, "value_usdc"] == 1.5
    assert isinstance(df.loc[0, "datetime"], pd.Timestamp)


def test_extract_timestamp_fallback_get_block(monkeypatch):
    monkeypatch.setattr(parser_module, "create_usdc_contract", lambda w3, contract_address: _FakeContract())
    raw_logs = [
        {
            "blockNumber": 100,
            "transactionHash": _FakeTxHash("0xdef"),
            "logIndex": 1,
            "mock_from": "0x0000000000000000000000000000000000000003",
            "mock_to": "0x0000000000000000000000000000000000000004",
            "mock_value": 2_000_000,
        }
    ]
    df = parser_module.parse_usdc_transfer_logs(
        w3=_FakeWeb3(),
        contract_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        raw_logs=raw_logs,
    )
    assert len(df) == 1
    assert df.loc[0, "timestamp"] == 1_700_000_000
