from __future__ import annotations

import os
from typing import Any

import requests


class LLMClient:
    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai_compatible")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "deepseek-v4-flash")
        self.timeout_seconds = 45

    def _build_endpoints(self) -> list[str]:
        """
        兼容不同 OpenAI-compatible 网关配置，自动尝试合理的 chat/completions 路径。
        """
        base = self.base_url.rstrip("/")
        endpoints: list[str] = []
        if base.endswith("/chat/completions"):
            endpoints.append(base)
        elif base.endswith("/v1") or base.endswith("/api/paas/v4"):
            endpoints.append(f"{base}/chat/completions")
        else:
            endpoints.append(f"{base}/chat/completions")
            if "open.bigmodel.cn" in base:
                endpoints.append(f"{base}/api/paas/v4/chat/completions")

        # 去重并保持顺序
        unique: list[str] = []
        for endpoint in endpoints:
            if endpoint not in unique:
                unique.append(endpoint)
        return unique

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        # 限制输入长度，避免部分网关在超长请求下返回 400。
        safe_user_prompt = user_prompt[:12000]
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": safe_user_prompt},
            ],
            "temperature": 0.2,
        }

    @staticmethod
    def _extract_error_detail(response: requests.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                err = data.get("error")
                if isinstance(err, dict):
                    code = err.get("code")
                    message = err.get("message")
                    if code or message:
                        return f"code={code}, message={message}"
                msg = data.get("message")
                if msg:
                    return str(msg)
        except Exception:
            pass
        text = response.text or ""
        return text[:500] if text else "<empty response body>"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("未配置 LLM_API_KEY。")
        payload = self._build_payload(system_prompt=system_prompt, user_prompt=user_prompt)
        last_error: Exception | None = None

        for endpoint in self._build_endpoints():
            try:
                response = requests.post(
                    endpoint,
                    headers=self._build_headers(),
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except requests.HTTPError as exc:
                last_error = exc
                status = exc.response.status_code if exc.response is not None else None
                detail = self._extract_error_detail(exc.response) if exc.response is not None else str(exc)
                # 405/404 多为路径问题，继续尝试下一候选地址
                if status in (404, 405):
                    continue
                raise RuntimeError(f"LLM HTTP错误 status={status}, endpoint={endpoint}, detail={detail}") from exc
            except Exception as exc:
                last_error = exc
                raise

        raise RuntimeError(
            f"LLM 请求失败，已尝试端点: {self._build_endpoints()}。最后错误: {last_error}"
        )
