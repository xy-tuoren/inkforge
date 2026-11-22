"""Abstract LLM interface and robust JSON parsing utilities."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


class LLMError(RuntimeError):
    """Raised when an LLM request fails or returns unparseable content."""


def extract_json(raw_text: str) -> Any:
    """Extract and parse a JSON object or array from an LLM response with resilience."""
    text = raw_text.strip()
    if not text:
        raise LLMError("模型返回为空，无法解析 JSON。")

    # 1. Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Balanced substring extraction ({...} or [...])
    start_idx = -1
    open_ch = ""
    close_ch = ""
    for i, ch in enumerate(text):
        if ch in "{[":
            start_idx = i
            open_ch = ch
            close_ch = "}" if ch == "{" else "]"
            break

    if start_idx >= 0:
        depth = 0
        in_str = False
        escape = False
        for j in range(start_idx, len(text)):
            c = text[j]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    candidate = text[start_idx : j + 1]
                    # Remove trailing commas before } or ]
                    repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
                    try:
                        return json.loads(repaired)
                    except json.JSONDecodeError:
                        break

    raise LLMError(f"无法从模型输出中提取合法 JSON（前 200 字）：{raw_text[:200]}")


class LLMClient(ABC):
    """Base interface for all LLM backends."""

    @abstractmethod
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
        """Generate a text completion."""

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task: str = "general",
        use_fast_model: bool = False,
        temperature: float = 0.4,
        max_tokens: int = 4096,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Generate and parse structured JSON with automatic one-shot repair retry."""
        raw = await self.complete(
            system_prompt,
            user_prompt,
            task=task,
            use_fast_model=use_fast_model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            metadata=metadata,
        )
        try:
            return extract_json(raw)
        except LLMError:
            repair_prompt = (
                "你刚才返回的内容不是合法 JSON。请只输出修复后的纯 JSON，不要附加任何解释或 Markdown：\n\n"
                f"{raw[:6000]}"
            )
            fixed = await self.complete(
                "你是一个严格的 JSON 格式化助手，只输出合法 JSON。",
                repair_prompt,
                task=f"{task}_json_repair",
                use_fast_model=True,
                temperature=0.0,
                max_tokens=max_tokens,
                json_mode=True,
                metadata=metadata,
            )
            return extract_json(fixed)
