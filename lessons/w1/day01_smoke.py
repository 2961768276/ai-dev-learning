import os
import time
import json,dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI(
    api_key=os.environ['DEEPSEEK_API_KEY'],
    base_url="https://api.deepseek.com",
)

start = time.time()

response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {"role": "user", "content": "用一句话介绍你自己"},
    ],
    stream=False,
)

os.makedirs("out", exist_ok=True)
with open("out/day01_resp.json", "w", encoding="utf-8") as f:
    json.dump(response.model_dump(), f, ensure_ascii=False, indent=2)
# 三个参数各自的作用
# resp.model_dump()：把 Pydantic 对象转成普通 dict，这是 json.dump 能接受的类型。
# ensure_ascii=False：必须加，否则 JSON 里的中文会变成 \u4f60\u597d 这种转义，打开看不懂。
# indent=2：格式化缩进，方便你打开文件后用眼睛检查结构。

latency = time.time() - start

print(response.choices[0].message.content)
print(response.usage.total_tokens)
print(f"latency: {latency:.2f}s")
