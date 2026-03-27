from __future__ import annotations

import os
from typing import List

from anthropic import Anthropic


def _extract_text_blocks(content_blocks: List) -> str:
    texts: List[str] = []
    for block in content_blocks:
        text = getattr(block, "text", "")
        if text:
            texts.append(text)
    return "\n".join(texts).strip()


def call_claude(prompt: str, model: str = "claude-sonnet-4-6", temperature: float = 0.2, max_tokens: int = 1400) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 ANTHROPIC_API_KEY，请先配置环境变量。")

    client = Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        raise RuntimeError(f"Claude API 调用失败：{exc}") from exc

    text = _extract_text_blocks(response.content)
    if not text:
        raise RuntimeError("Claude API 返回为空，请重试或检查模型配置。")
    return text
