"""DeepSeek 统一 LLM 客户端（Day 3）。

对外契约（与 8 周计划一致）::

    chat(messages, **kw) -> {
        "content":     str,          # 完整内容，不要截断，调用方直接用
        "usage":       {...},        # prompt/completion/total/reasoning/cached
        "latency_s":   float,
        "model":       str,          # 以服务端返回为准，便于核对真实模型
        "finish_reason": str,        # "stop" / "length" → length 说明被截断
        "request_id":  str | None,   # 找服务商对账、报障时的凭据
    }

工程约定：
- 配置全部来自 `.env`，代码里不写死 model / base_url / 超时（换模型只改环境变量）。
- import 无副作用：没有 API Key 也能 import，只有真正调用才报配置错，CI 不会被 env 卡住。
- 每次调用追加一行 JSONL 到 `logs/usage.jsonl`，失败追加一行到 `logs/errors.jsonl`；
  jsonl 是成本与延迟的唯一事实来源，print 只用于人看。
- 超时与重试交给 SDK（`timeout` / `max_retries`）；Day 6 再补错误分类与退避日志。
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
LOG_DIR = PROJECT_ROOT / "logs"
USAGE_LOG = LOG_DIR / "usage.jsonl"
ERROR_LOG = LOG_DIR / "errors.jsonl"

# 只补充缺失的变量，不覆盖已有值：容器 / CI / shell 里显式设置的值优先。
load_dotenv(ENV_FILE)

PREVIEW_CHARS = 40
DEFAULT_BASE_URL = "https://api.deepseek.com"
# 模型名会随服务商迭代下线，旧 id 可能直接失效。这里只放"兜底默认值"，
# 真正的选择在 .env 的 LLM_MODEL；不确定当前有哪些模型就跑 scripts/list_models.py。
DEFAULT_MODEL = "deepseek-flash"  # 4.1，快且便宜，日常默认
STRONG_MODEL = "deepseek-v4-pro"  # v4，推理更强，留给难任务与对照实验


class MissingConfigError(RuntimeError):
    """缺少必需配置（如 API Key）时抛出，提示文案要能直接照着做。"""


@dataclass(frozen=True)
class LLMSettings:
    """一次运行内不变的 LLM 配置。新增参数时只改这里 + .env.example。"""

    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout_s: float
    max_retries: int

    @classmethod
    def from_env(cls) -> LLMSettings:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise MissingConfigError(
                "缺少 DEEPSEEK_API_KEY：先执行 `cp .env.example .env` 并填入真实 Key"
                "（.env 已被 .gitignore 拦截，不会进仓库）"
            )
        return cls(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL),
            temperature=_env_float("LLM_TEMPERATURE", 0.2) or 0.0,
            max_tokens=_env_int("LLM_MAX_TOKENS", 1024),
            timeout_s=_env_float("LLM_TIMEOUT_S", 30.0) or 30.0,
            max_retries=_env_int("LLM_MAX_RETRIES", 2),
        )


def _env_float(name: str, default: float | None = None) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """进程内复用同一个 HTTP 连接池；改了 .env 需要重启进程。"""
    settings = LLMSettings.from_env()
    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=settings.timeout_s,
        max_retries=settings.max_retries,
    )


def list_models() -> list[str]:
    """向服务商确认当前可用的模型 id：模型名不要凭记忆写，直接问接口。"""
    return [model.id for model in get_client().models.list().data]


def chat(messages: list[dict[str, Any]], **kw: Any) -> dict[str, Any]:
    """调一次 DeepSeek Chat Completions，记账后返回统一结构。

    `**kw` 里允许覆盖 model / temperature / max_tokens，其余（top_p、stop、seed、
    response_format、tools…）原样透传给 SDK，方便 Day 2/5/12 各天的实验复用。
    """
    if not messages:
        raise ValueError("messages 不能为空：至少要有 1 条 {'role': ..., 'content': ...}")

    settings = LLMSettings.from_env()
    payload: dict[str, Any] = {
        "model": kw.pop("model", settings.model),
        "temperature": kw.pop("temperature", settings.temperature),
        "max_tokens": kw.pop("max_tokens", settings.max_tokens),
        "messages": messages,
        "stream": False,
    }
    payload.update(kw)

    prompt_preview = _preview(str(messages[-1].get("content", "")))
    start = time.perf_counter()
    try:
        response = get_client().chat.completions.create(**payload)
    except Exception as exc:  # 记录后原样抛给调用方，由它决定是重试还是展示
        _write_jsonl(
            ERROR_LOG,
            {
                "time": _now(),
                "model": payload["model"],
                "error_type": type(exc).__name__,
                "status_code": getattr(exc, "status_code", None),
                "message": str(exc)[:500],
                "latency_s": round(time.perf_counter() - start, 3),
                "prompt_preview": prompt_preview,
            },
        )
        raise

    latency_s = round(time.perf_counter() - start, 3)
    choice = response.choices[0]
    usage = _usage_dict(response.usage)
    result: dict[str, Any] = {
        "content": choice.message.content or "",
        "usage": usage,
        "latency_s": latency_s,
        "model": response.model or payload["model"],
        "finish_reason": choice.finish_reason,
        "request_id": getattr(response, "id", None),
    }
    _write_jsonl(
        USAGE_LOG,
        {
            "time": _now(),
            "request_id": result["request_id"],
            "model": result["model"],
            "finish_reason": result["finish_reason"],
            **usage,
            "latency_s": latency_s,
            "prompt_preview": prompt_preview,
            "content_preview": _preview(result["content"]),
        },
    )
    return result


def read_usage_rows(path: Path | None = None) -> list[dict[str, Any]]:
    """读取 usage 日志；坏行跳过，不让一行脏数据把报表打挂。"""
    log_path = path or USAGE_LOG
    if not log_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def daily_summary(day: str | None = None, path: Path | None = None) -> dict[str, Any]:
    """汇总某天（默认今天）的调用次数、token、平均延迟与估算花费。

    兼容两种历史格式：Day 3 之前的扁平行（prompt_tokens 在顶层）与之后的
    嵌套行（usage.prompt_tokens），因为日志格式演进时不能丢历史成本数据。
    """
    target = day or datetime.now().strftime("%Y-%m-%d")
    rows = [row for row in read_usage_rows(path) if str(row.get("time", "")).startswith(target)]

    prompt = completion = reasoning = 0
    total_latency = 0.0
    models: set[str] = set()
    for row in rows:
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else row
        prompt += int(usage.get("prompt_tokens") or 0)
        completion += int(usage.get("completion_tokens") or 0)
        reasoning += int(usage.get("reasoning_tokens") or 0)
        total_latency += float(row.get("latency_s") or 0.0)
        if row.get("model"):
            models.add(str(row["model"]))

    cost = estimate_cost(prompt, completion)
    return {
        "day": target,
        "calls": len(rows),
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "reasoning_tokens": reasoning,
        "total_tokens": prompt + completion,
        "avg_latency_s": round(total_latency / len(rows), 3) if rows else 0.0,
        "models": sorted(models),
        "cost": cost,
        "currency": os.getenv("LLM_PRICE_CURRENCY", "CNY"),
    }


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float | None:
    """按 .env 的单价估算花费；没配单价就返回 None，绝不硬编码一个猜的价格。"""
    price_in = _env_float("LLM_PRICE_INPUT_PER_M")
    price_out = _env_float("LLM_PRICE_OUTPUT_PER_M")
    if price_in is None or price_out is None:
        return None
    return round(
        prompt_tokens / 1_000_000 * price_in + completion_tokens / 1_000_000 * price_out,
        6,
    )


def _usage_dict(usage: Any) -> dict[str, int]:
    """把 SDK 的 usage 摊平成固定字段，缺字段补 0，方便后面直接 sum。"""
    if usage is None:
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "cached_tokens": 0,
        }
    completion_details = getattr(usage, "completion_tokens_details", None)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    return {
        "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
        "reasoning_tokens": int(getattr(completion_details, "reasoning_tokens", 0) or 0),
        "cached_tokens": int(getattr(prompt_details, "cached_tokens", 0) or 0),
    }


def _preview(text: str) -> str:
    """日志里只留摘要，避免把长文本（可能含用户隐私）整段落盘。"""
    return " ".join(text.split())[:PREVIEW_CHARS]


def _now() -> str:
    """带时区的本地时间：跨机器、跨时区看日志时不用猜。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
