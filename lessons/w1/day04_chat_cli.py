
from __future__ import annotations
import json
from pathlib import Path

from ai_dev_learning.common.llm import chat, daily_summary

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "out"
RESP_FILE = OUT_DIR / "day04_history.json"

def main() -> None:
    messages = [
        {"role": "system", "content": "你是一个苏格拉底式提问者。规则：永远不直接给出答案；每次回复必须以一个反问结尾，引导用户自己思考。"}
    ]
    while True:
        user_input = input("你> ")
        if user_input == "exit": 
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            RESP_FILE.write_text(
                    json.dumps(messages, ensure_ascii=False),
                    encoding="utf-8",
                )
            break
        messages.append({"role": "user", "content": user_input})
        reply = chat(messages)
        print(reply["content"])
        messages.append({"role": "assistant", "content": reply["content"]})

    

    
if __name__ == "__main__":
    main()
