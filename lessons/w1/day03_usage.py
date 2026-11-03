"""Day 3：连跑 3 次，验证统一客户端的 usage 记账与当日累计。

看点：
1. 同一 prompt 三次的 token / 延迟差异（成本与性能不是常数）；
2. `logs/usage.jsonl` 每行都能追到 request_id，出问题能拿它找服务商对账；
3. 当日累计来自 jsonl 而不是内存计数 —— 进程重启、换终端也不丢账。

运行（任意目录都可以）：
    uv run python lessons/w1/day03_usage.py

注意：累计值统计的是"今天所有走 common/llm.py 的调用"，包含 day02 的参数实验。
"""

from __future__ import annotations

from ai_dev_learning.common.llm import chat, daily_summary

PROMPT = "用一句话介绍下你自己。"
ROUNDS = 3


def main() -> None:
    for i in range(1, ROUNDS + 1):
        result = chat([{"role": "user", "content": PROMPT}])
        usage = result["usage"]
        print(
            f"[{i}/{ROUNDS}] {result['latency_s']:.2f}s "
            f"prompt={usage['prompt_tokens']} completion={usage['completion_tokens']} "
            f"total={usage['total_tokens']} | {result['content'][:30]}"
        )

    summary = daily_summary()
    print(
        f"\n{summary['day']} 累计：{summary['calls']} 次调用，"
        f"total_tokens={summary['total_tokens']}"
        f"（prompt={summary['prompt_tokens']}, completion={summary['completion_tokens']}），"
        f"平均 {summary['avg_latency_s']:.2f}s/次，模型={','.join(summary['models']) or '无'}"
    )
    if summary["cost"] is None:
        print("花费：未配置 LLM_PRICE_INPUT_PER_M / LLM_PRICE_OUTPUT_PER_M，跳过估算（不猜价格）")
    else:
        print(f"花费：约 {summary['cost']} {summary['currency']}（按 .env 单价估算）")


if __name__ == "__main__":
    main()
