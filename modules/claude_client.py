from __future__ import annotations

import os
from typing import List, Tuple

import streamlit as st
from anthropic import Anthropic


def _extract_text_blocks(content_blocks: List) -> str:
    texts: List[str] = []
    for block in content_blocks:
        text = getattr(block, "text", "")
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


def _read_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, "")


def get_claude_config() -> Tuple[str, str]:
    api_key = _read_secret("ANTHROPIC_API_KEY").strip()
    base_url = _read_secret("BASE_URL").strip()
    return api_key, base_url


def is_ai_configured() -> bool:
    api_key, _ = get_claude_config()
    return bool(api_key)


def call_claude(prompt: str, model: str = "claude-sonnet-4-6", temperature: float = 0.2, max_tokens: int = 1400) -> str:
    api_key, base_url = get_claude_config()
    if not api_key:
        raise RuntimeError("未检测到 ANTHROPIC_API_KEY 配置，请在 Streamlit secrets 或环境变量中设置。")

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = Anthropic(**client_kwargs)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise RuntimeError("Claude API 调用失败，请检查网络、密钥或 BASE_URL 配置。") from exc

    text = _extract_text_blocks(response.content)
    if not text:
        raise RuntimeError("Claude API 返回为空，请重试或检查模型配置。")
    return text
