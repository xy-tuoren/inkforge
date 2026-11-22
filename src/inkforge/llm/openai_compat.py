"""OpenAI-compatible async client supporting DeepSeek, Doubao, Qwen, OpenAI, OpenRouter, Ollama."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from inkforge.config import PROVIDER_PRESETS, LLMConfig
from inkforge.llm.base import LLMClient, LLMError


class OpenAICompatClient(LLMClient):
    def __init__(self, config: LLMConfig) -> None:
        self.config = config.resolved()
        preset = PROVIDER_PRESETS.get(self.config.provider, PROVIDER_PRESETS["custom"])
        if preset.requires_api_key and not self.config.api_key:
            raise LLMError(
                f"当前模型服务【{preset.label}】需要配置 API Key。"
                "请在 .env 中设置 INKFORGE_API_KEY，或在 Web 工作室「模型设置」中填写；"
                "若只想先离线体验，可将 provider 切换为 demo。"
            )
        if not self.config.base_url:
            raise LLMError("未配置有效的 Base URL。")

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task: str = "general",
        use_fast_model: bool = False,
        temperature: float | None = None,
        max_tokens: int = 4096,
        json_mode: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        url = self.config.base_url.rstrip("/") + "/chat/completions"
        model_name = self.config.fast_model if use_fast_model else self.config.model
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature if temperature is None else temperature,
            "max_tokens": max_tokens,
        }
        if json_mode and self.config.provider in ("openai", "deepseek", "qwen", "doubao"):
            payload["response_format"] = {"type": "json_object"}

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                    resp = await client.post(url, headers=headers, json=payload)

                if resp.status_code == 400 and json_mode and "response_format" in payload:
                    # Some custom/proxy endpoints reject response_format; retry cleanly without it
                    payload.pop("response_format", None)
                    continue

                if resp.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue

                if resp.status_code >= 400:
                    detail = resp.text[:400]
                    raise LLMError(f"模型接口请求失败（HTTP {resp.status_code}）：{detail}")

                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    raise LLMError("模型响应缺少 choices 字段。")
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise LLMError("模型返回了空内容。")
                return content.strip()
            except httpx.HTTPError as exc:
                last_err = exc
                if attempt < 2:
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                raise LLMError(f"网络连接模型服务失败：{type(exc).__name__}: {exc}") from exc

        raise LLMError(f"模型请求重试后仍失败：{last_err}")
