"""Day 1：第一次云端调用跑通。

目的：看清 OpenAI SDK 的原貌 —— content、usage.total_tokens、耗时，并把原始响应
落盘作为证据。这一天的脚本故意不经过 `common/llm.py`（那是 Day 3 的事），
后面所有脚本再统一走共享客户端。

运行（任意目录都可以）：
    uv run python lessons/w1/day01_smoke.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "out"
RESP_FILE = OUT_DIR / "day01_resp.json"

load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("缺少 DEEPSEEK_API_KEY：先 `cp .env.example .env` 并填入真实 Key")

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        timeout=float(os.getenv("LLM_TIMEOUT_S", "30")),
        max_retries=0,  # 冒烟脚本要一次看清真实错误，不要让 SDK 自动重试掩盖问题
    )

    requested_model = os.getenv("LLM_MODEL", "deepseek-chat")
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=requested_model,
        messages=[{"role": "user", "content": "用一句话介绍你自己"}],
        stream=False,
    )
    latency_s = time.perf_counter() - start

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESP_FILE.write_text(
        json.dumps(response.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # model_dump()：Pydantic 对象转 dict，json.dump 只认 dict/list/str/int。
    # ensure_ascii=False：否则中文变 \u4f60\u597d，打开看不懂。
    # indent=2：格式化，方便用眼睛检查结构。

    choice = response.choices[0]
    print(f"model        : 请求 {requested_model} → 返回 {response.model}")
    print(f"content      : {choice.message.content}")
    print(f"finish_reason: {choice.finish_reason}")
    usage = response.usage
    usage_dump = usage.model_dump() if hasattr(usage, "model_dump") else usage
    print(f"usage        : {usage_dump}")
    print(f"latency      : {latency_s:.2f}s")
    print(f"raw response : {RESP_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
