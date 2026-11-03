"""Day 2：参数控制 —— temperature / max_tokens / finish_reason。

同一句 prompt 跑一遍参数网格，把结果写成可展示的 Markdown 表格。
- temperature=0 跑两次：验证"钉死 0"到底能不能复现（计划复盘问题②）。
- max_tokens=20：观察截断，看 finish_reason=length 时 content 还剩什么。

注意：本脚本走 `common/llm.py`，所以这 5 次调用同样会记进 `logs/usage.jsonl`
（实验也是花钱的，成本台账不能漏）。

运行（任意目录都可以）：
    uv run python lessons/w1/day02_params.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_dev_learning.common.llm import chat

OUT_MD = Path(__file__).resolve().parent / "out" / "day02_params.md"
PROMPT = "用一句话介绍你自己。"

CASES: list[dict[str, Any]] = [
    {"label": "A", "note": "基线 #1（temperature=0）", "temperature": 0.0},
    {"label": "B", "note": "基线 #2（复现性对照）", "temperature": 0.0},
    {"label": "C", "note": "默认创意档", "temperature": 0.7},
    {"label": "D", "note": "高随机", "temperature": 1.3},
    {"label": "E", "note": "硬截断（max_tokens=20）", "max_tokens": 20},
]


def _cell(text: str, limit: int = 40) -> str:
    """表格单元格：干掉换行、转义竖线，否则整个 Markdown 表格会错行。"""
    flat = " ".join(text.split())
    if len(flat) > limit:
        flat = flat[:limit] + "…"
    return flat.replace("|", "\\|") or "（空）"


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    params = {k: case[k] for k in ("temperature", "max_tokens") if k in case}
    result = chat([{"role": "user", "content": PROMPT}], **params)
    usage = result["usage"]
    row = {
        "label": case["label"],
        "note": case["note"],
        "model": result["model"],  # 记录实际模型：换 flash / v4-pro 时表格才说得清
        "temperature": params.get("temperature", "默认"),
        "max_tokens": params.get("max_tokens", "默认"),
        "finish_reason": result["finish_reason"],
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "reasoning_tokens": usage["reasoning_tokens"],
        "total_tokens": usage["total_tokens"],
        "latency_s": result["latency_s"],
        "content": result["content"],
    }
    print(
        f"[{row['label']}] temp={row['temperature']} max_tokens={row['max_tokens']}"
        f" finish={row['finish_reason']} total={row['total_tokens']}"
        f" {row['latency_s']}s | {_cell(row['content'], 30)}"
    )
    return row


def build_markdown(rows: list[dict[str, Any]]) -> str:
    header = (
        "| 组别 | 模型 | 说明 | temperature | max_tokens | finish_reason "
        "| prompt | completion | reasoning | total | 耗时(s) | 输出（前 40 字） |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    body = "".join(
        f"| {r['label']} | {r['model']} | {r['note']} | {r['temperature']} | {r['max_tokens']} "
        f"| {r['finish_reason']} | {r['prompt_tokens']} | {r['completion_tokens']} "
        f"| {r['reasoning_tokens']} | {r['total_tokens']} | {r['latency_s']} "
        f"| {_cell(r['content'])} |\n"
        for r in rows
    )
    return header + body + conclusion(rows)


def conclusion(rows: list[dict[str, Any]]) -> str:
    """结论按真实结果生成，不写死一句漂亮话。"""
    by_label = {r["label"]: r for r in rows}
    a, b = by_label["A"], by_label["B"]
    same = a["content"].strip() == b["content"].strip()
    truncated = [r for r in rows if r["finish_reason"] == "length"]

    if same:
        repeat_note = "该模型在 0 档是确定性的"
    else:
        repeat_note = (
            "即使 temperature=0 仍有波动（思考型模型的 reasoning 段也会影响结果），"
            "要复现还得固定 seed 或重试取一致项"
        )
    verdict = "完全一致" if same else "**并不完全一致**"
    lines = [
        "",
        "## 结论",
        "",
        f"- temperature=0 两次输出{verdict}：说明{repeat_note}。",
    ]
    if truncated:
        r = truncated[0]
        lines.append(
            f"- `finish_reason=length` 代表输出被 `max_tokens={r['max_tokens']}` 截断，"
            f"不是模型答完了；本次 completion_tokens={r['completion_tokens']}，"
            f"其中 reasoning_tokens={r['reasoning_tokens']}，"
            f"真正的正文只剩「{_cell(r['content'])}」。"
        )
        if not r["content"].strip():
            lines.append(
                "- 截断时 content 为空不是 bug：思考型模型的 reasoning token 也计入 max_tokens，"
                "预算被“想”吃光后就没有正文了。生产环境的对策：给足 max_tokens，"
                "并用 finish_reason 判定是否重试或降级。"
            )
    lines.append(
        "- 业务上要把 temperature 钉死在 0 的场景：字段抽取、分类/打标、代码生成、"
        "任何要写进数据库或触发下游动作的结果 —— 宁可重复也不能漂移。"
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    rows = [run_case(case) for case in CASES]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(build_markdown(rows), encoding="utf-8")
    print(f"\n已写入 {OUT_MD}")


if __name__ == "__main__":
    main()
