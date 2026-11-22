"""Configuration & LLM provider presets for InkForge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ProviderPreset:
    id: str
    label: str
    base_url: str
    default_model: str
    fast_model: str
    requires_api_key: bool
    hint: str


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "demo": ProviderPreset(
        id="demo",
        label="内置演示引擎（离线免 Key）",
        base_url="",
        default_model="inkforge-demo-v1",
        fast_model="inkforge-demo-v1",
        requires_api_key=False,
        hint="零成本离线体验完整「设定集 → 分镜 → 初稿 → 去AI味红笔体检 → 精修对比 → EPUB导出」全链路。",
    ),
    "deepseek": ProviderPreset(
        id="deepseek",
        label="DeepSeek 官方 API",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        fast_model="deepseek-chat",
        requires_api_key=True,
        hint="中文叙事与对话表现优异、性价比极高；推荐 deepseek-chat / deepseek-reasoner。",
    ),
    "doubao": ProviderPreset(
        id="doubao",
        label="火山方舟 · 豆包 (Doubao)",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        default_model="doubao-1-5-pro-32k-250115",
        fast_model="doubao-1-5-lite-32k-250115",
        requires_api_key=True,
        hint="火山方舟 OpenAI 兼容接口，Model 字段可填模型名或推理接入点 ID（ep-xxxx）。",
    ),
    "qwen": ProviderPreset(
        id="qwen",
        label="阿里云百炼 · 通义千问 (Qwen)",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-max",
        fast_model="qwen-plus",
        requires_api_key=True,
        hint="长上下文稳定、中文古典与都市题材适应性强。",
    ),
    "openai": ProviderPreset(
        id="openai",
        label="OpenAI API",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4.1",
        fast_model="gpt-4.1-mini",
        requires_api_key=True,
        hint="支持 GPT-4.1 / GPT-4o / o3 等模型。",
    ),
    "openrouter": ProviderPreset(
        id="openrouter",
        label="OpenRouter 聚合网关",
        base_url="https://openrouter.ai/api/v1",
        default_model="anthropic/claude-sonnet-4",
        fast_model="google/gemini-2.5-flash",
        requires_api_key=True,
        hint="一个 Key 接入 Claude / Gemini / DeepSeek / GPT，强烈推荐 Claude Sonnet 写长篇文笔。",
    ),
    "ollama": ProviderPreset(
        id="ollama",
        label="本地 Ollama（隐私离线）",
        base_url="http://127.0.0.1:11434/v1",
        default_model="qwen2.5:14b",
        fast_model="qwen2.5:7b",
        requires_api_key=False,
        hint="完全本地运行，需提前启动 Ollama 并拉取模型。",
    ),
    "custom": ProviderPreset(
        id="custom",
        label="自定义 OpenAI 兼容接口",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o",
        fast_model="gpt-4o-mini",
        requires_api_key=True,
        hint="兼容任意支持 /v1/chat/completions 的代理或私有部署 vLLM / OneAPI。",
    ),
}


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


class LLMConfig(BaseModel):
    provider: str = "demo"
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    fast_model: str = ""
    temperature: float = Field(default=0.78, ge=0.0, le=1.5)
    timeout_seconds: float = Field(default=120.0, ge=10.0, le=600.0)

    def resolved(self) -> LLMConfig:
        preset = PROVIDER_PRESETS.get(self.provider, PROVIDER_PRESETS["custom"])
        return LLMConfig(
            provider=self.provider,
            api_key=self.api_key,
            base_url=self.base_url or preset.base_url,
            model=self.model or preset.default_model,
            fast_model=self.fast_model or self.model or preset.fast_model,
            temperature=self.temperature,
            timeout_seconds=self.timeout_seconds,
        )

    def safe_dict(self) -> dict[str, Any]:
        r = self.resolved()
        masked = ""
        if r.api_key:
            masked = (
                f"{r.api_key[:4]}...{r.api_key[-4:]}"
                if len(r.api_key) > 10
                else "****"
            )
        return {
            "provider": r.provider,
            "has_api_key": bool(r.api_key),
            "api_key_masked": masked,
            "base_url": r.base_url,
            "model": r.model,
            "fast_model": r.fast_model,
            "temperature": r.temperature,
        }


class AppSettings(BaseModel):
    data_dir: Path = Path(".inkforge")
    llm: LLMConfig = Field(default_factory=LLMConfig)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "inkforge.db"

    @property
    def settings_file(self) -> Path:
        return self.data_dir / "settings.json"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def save_llm_config(self, cfg: LLMConfig) -> None:
        self.ensure_dirs()
        self.llm = cfg
        self.settings_file.write_text(
            json.dumps(cfg.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def load_settings(data_dir: Path | str | None = None) -> AppSettings:
    _load_dotenv(Path.cwd() / ".env")
    resolved_dir = Path(
        data_dir
        or os.getenv("INKFORGE_DATA_DIR")
        or ".inkforge"
    )
    settings_file = resolved_dir / "settings.json"

    llm_cfg = LLMConfig(
        provider=os.getenv("INKFORGE_PROVIDER", "demo").strip().lower(),
        api_key=os.getenv("INKFORGE_API_KEY", "").strip(),
        base_url=os.getenv("INKFORGE_BASE_URL", "").strip(),
        model=os.getenv("INKFORGE_MODEL", "").strip(),
        fast_model=os.getenv("INKFORGE_FAST_MODEL", "").strip(),
    )

    # Local settings.json saved from Web UI overrides defaults when present
    if settings_file.exists():
        try:
            saved = json.loads(settings_file.read_text(encoding="utf-8"))
            llm_cfg = LLMConfig(**{**llm_cfg.model_dump(), **saved})
        except Exception:
            pass

    app_settings = AppSettings(data_dir=resolved_dir, llm=llm_cfg)
    app_settings.ensure_dirs()
    return app_settings
