"""打印当前账号可用的模型列表。

模型名会下线、改名（例如 deepseek-chat 已经停用），写死之前先跑这个：
    uv run python scripts/list_models.py

返回里没有的模型名，调用时只会得到 400/404，不要靠猜。
"""

from __future__ import annotations

from ai_dev_learning.common.llm import LLMSettings, list_models


def main() -> None:
    settings = LLMSettings.from_env()
    print(f"base_url = {settings.base_url}")
    print(f".env 里 LLM_MODEL = {settings.model}")
    for model in list_models():
        print(f"- {model}")


if __name__ == "__main__":
    main()
