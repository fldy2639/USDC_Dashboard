import pandas as pd

from agent.anomaly_detector import detect_anomalies
from agent.metrics_builder import build_metrics_summary
from agent.report_agent import generate_agent_report


def _sample_df() -> pd.DataFrame:
    rows = [
        {
            "transaction_hash": "0xaa",
            "block_number": 10,
            "log_index": 0,
            "from": "0x0000000000000000000000000000000000000001",
            "to": "0x0000000000000000000000000000000000000002",
            "value_raw": 2_000_000_000_000,
            "value_usdc": 2_000_000.0,
            "timestamp": 1_700_000_000,
            "datetime": "2023-11-14 22:13:20+00:00",
            "date": "2023-11-14",
        },
        {
            "transaction_hash": "0xbb",
            "block_number": 11,
            "log_index": 0,
            "from": "0x0000000000000000000000000000000000000002",
            "to": "0x0000000000000000000000000000000000000001",
            "value_raw": 500_000_000_000,
            "value_usdc": 500_000.0,
            "timestamp": 1_700_000_060,
            "datetime": "2023-11-14 22:14:20+00:00",
            "date": "2023-11-14",
        },
    ]
    return pd.DataFrame(rows)


def test_build_metrics_summary():
    df = _sample_df()
    metrics = build_metrics_summary(
        df=df,
        target_address="0x0000000000000000000000000000000000000001",
        whale_threshold=1_000_000,
    )
    assert metrics["market_activity"]["transfer_count"] == 2
    assert metrics["market_activity"]["whale_transfer_count"] == 1
    assert metrics["target_address"]["net_flow_usdc"] == -1_500_000.0


def test_detect_anomalies():
    df = _sample_df()
    metrics = build_metrics_summary(df=df, target_address="", whale_threshold=1_000_000)
    anomalies = detect_anomalies(df=df, metrics=metrics, whale_threshold=1_000_000, high_activity_threshold=1)
    assert any(item["type"] == "whale_transfer" for item in anomalies)
    assert any(item["type"] == "high_activity" for item in anomalies)


def test_generate_agent_report_fallback():
    df = _sample_df()
    result = generate_agent_report(
        df=df,
        target_address="0x0000000000000000000000000000000000000001",
        whale_threshold=1_000_000,
    )
    assert "report_markdown" in result
    assert "metrics" in result
