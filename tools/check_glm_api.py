#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


def _safe_json_text(resp: requests.Response, limit: int = 1200) -> str:
    try:
        return json.dumps(resp.json(), ensure_ascii=False, indent=2)[:limit]
    except Exception:
        return (resp.text or "")[:limit]


def _print_result(title: str, ok: bool, detail: str) -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {title}")
    print(detail)
    print("-" * 80)


def main() -> int:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_key:
        print("未配置 LLM_API_KEY")
        return 2
    if not base_url:
        print("未配置 LLM_BASE_URL")
        return 2
    if not model:
        print("未配置 LLM_MODEL")
        return 2

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    print(f"Using base_url={base_url}")
    print(f"Using model={model}")
    print("=" * 80)

    # 1) 检查 models 列表能力（部分网关可能不支持，但可用于快速判断权限/鉴权）
    models_url = f"{base_url}/models"
    try:
        resp = requests.get(models_url, headers=headers, timeout=25)
        ok = resp.status_code == 200
        _print_result(
            "GET /models",
            ok,
            f"status={resp.status_code}\nbody={_safe_json_text(resp)}",
        )
    except Exception as exc:
        _print_result("GET /models", False, f"exception={exc}")

    # 2) 最小 chat/completions 请求
    chat_url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好，请回复：ok"}],
        "temperature": 0.2,
        "max_tokens": 32,
    }
    try:
        resp = requests.post(chat_url, headers=headers, json=payload, timeout=30)
        ok = resp.status_code == 200
        _print_result(
            "POST /chat/completions (smoke test)",
            ok,
            f"status={resp.status_code}\nbody={_safe_json_text(resp)}",
        )
    except Exception as exc:
        _print_result("POST /chat/completions (smoke test)", False, f"exception={exc}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
