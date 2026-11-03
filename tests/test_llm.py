"""common/llm.py 的单元测试（Day 3 的工程底线）。

全部用假的 OpenAI 客户端：不联网、不花钱，
所以能在 CI（没有 API Key）里跑通。
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ai_dev_learning.common import llm


class FakeCompletions:
    """记录调用参数，返回预置响应；设置 exc 时模拟上游报错。"""

    def __init__(self, response: Any = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.exc is not None:
            raise self.exc
        return self.response


def make_response(
    content: str | None = "你好",
    finish_reason: str = "stop",
    model: str = "deepseek-chat",
    request_id: str = "req_test_1",
) -> Any:
    usage = SimpleNamespace(
        prompt_tokens=11,
        completion_tokens=7,
        total_tokens=18,
        completion_tokens_details=SimpleNamespace(reasoning_tokens=2),
        prompt_tokens_details=SimpleNamespace(cached_tokens=0),
    )
    message = SimpleNamespace(content=content)
    return SimpleNamespace(
        id=request_id,
        model=model,
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        usage=usage,
    )


def fake_chat(fake: FakeCompletions) -> SimpleNamespace:
    return SimpleNamespace(chat=SimpleNamespace(completions=fake))


def install(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake: FakeCompletions,
) -> FakeCompletions:
    """把客户端和日志路径都换成临时对象，测试互不污染。"""
    monkeypatch.setattr(llm, "get_client", lambda: fake_chat(fake))
    monkeypatch.setattr(llm, "USAGE_LOG", tmp_path / "usage.jsonl")
    monkeypatch.setattr(llm, "ERROR_LOG", tmp_path / "errors.jsonl")
    return fake


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> FakeCompletions:
    return install(monkeypatch, tmp_path, FakeCompletions(response=make_response()))


def read_lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_chat_returns_contract_and_writes_usage_log(fake_client: FakeCompletions) -> None:
    result = llm.chat([{"role": "user", "content": "打印这一条就别截断我"}])

    assert set(result) >= {"content", "usage", "latency_s", "model", "finish_reason", "request_id"}
    assert result["content"] == "你好"  # 完整内容，不能像旧版那样截成 40 字
    assert result["usage"]["total_tokens"] == 18
    assert result["usage"]["reasoning_tokens"] == 2
    assert result["finish_reason"] == "stop"
    assert result["latency_s"] >= 0

    rows = read_lines(llm.USAGE_LOG)
    assert len(rows) == 1
    assert rows[0]["request_id"] == "req_test_1"
    assert rows[0]["total_tokens"] == 18
    assert "T" in rows[0]["time"]  # 带 T 和时区，跨机器可读
    assert rows[0]["content_preview"] == "你好"


def test_kw_passthrough_and_env_defaults(
    fake_client: FakeCompletions, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LLM_MODEL", "deepseek-flash")
    fake_client.response = make_response(model="deepseek-flash")

    llm.chat(
        [{"role": "user", "content": "hi"}],
        temperature=0,
        max_tokens=20,
        seed=42,
        top_p=0.9,
    )

    payload = fake_client.calls[0]
    assert payload["model"] == "deepseek-flash"  # 来自 .env，不是硬编码
    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 20
    assert payload["seed"] == 42
    assert payload["top_p"] == 0.9  # 其余参数原样透传
    assert payload["stream"] is False


def test_empty_messages_rejected_before_network(fake_client: FakeCompletions) -> None:
    with pytest.raises(ValueError, match="messages 不能为空"):
        llm.chat([])
    assert fake_client.calls == []


def test_error_is_logged_and_reraised(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = FakeCompletions(exc=RuntimeError("429 rate limited"))
    install(monkeypatch, tmp_path, fake)

    with pytest.raises(RuntimeError, match="429"):
        llm.chat([{"role": "user", "content": "hi"}])

    errors = read_lines(tmp_path / "errors.jsonl")
    assert len(errors) == 1
    assert errors[0]["error_type"] == "RuntimeError"
    assert "429" in errors[0]["message"]
    assert not (tmp_path / "usage.jsonl").exists()  # 失败不计入成功账本


def test_none_content_becomes_empty_string(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = FakeCompletions(response=make_response(content=None, finish_reason="length"))
    install(monkeypatch, tmp_path, fake)

    result = llm.chat([{"role": "user", "content": "hi"}], max_tokens=20)
    assert result["content"] == ""
    assert result["finish_reason"] == "length"


def test_missing_api_key_has_actionable_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(llm.MissingConfigError, match="cp .env.example .env"):
        llm.LLMSettings.from_env()


def test_daily_summary_reads_both_log_formats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "usage.jsonl"
    rows = [
        # Day 3 之前的扁平行
        {
            "time": "2026-11-02T10:00:00",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_s": 1.0,
        },
        # 新格式
        {
            "time": "2026-11-02T11:00:00",
            "model": "deepseek-flash",
            "usage": {"prompt_tokens": 20, "completion_tokens": 8, "reasoning_tokens": 3},
            "latency_s": 3.0,
        },
        {"time": "2026-11-03T09:00:00", "usage": {"prompt_tokens": 99, "completion_tokens": 1}},
    ]
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n{not json}\n", encoding="utf-8")
    monkeypatch.delenv("LLM_PRICE_INPUT_PER_M", raising=False)
    monkeypatch.delenv("LLM_PRICE_OUTPUT_PER_M", raising=False)

    summary = llm.daily_summary(day="2026-11-02", path=log)

    assert summary["calls"] == 2
    assert summary["prompt_tokens"] == 30
    assert summary["completion_tokens"] == 13
    assert summary["total_tokens"] == 43
    assert summary["reasoning_tokens"] == 3
    assert summary["avg_latency_s"] == 2.0
    assert summary["models"] == ["deepseek-flash"]
    assert summary["cost"] is None


def test_estimate_cost_uses_configured_prices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PRICE_INPUT_PER_M", "1")
    monkeypatch.setenv("LLM_PRICE_OUTPUT_PER_M", "2")

    assert llm.estimate_cost(1_000_000, 500_000) == pytest.approx(2.0)
