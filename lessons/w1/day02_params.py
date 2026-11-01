import os
import time
import json,dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI(
    api_key=os.environ['DEEPSEEK_API_KEY'],
    base_url="https://api.deepseek.com",
)

def run(label,**kws):
    response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {"role": "user", "content": "用一句话介绍你自己"},
    ],
    stream=False,
    **kws
    )
    print(f"{label} | temp = {kws.get('temperature')} | finish_reason={response.choices[0].finish_reason} | total_tokens={response.usage.total_tokens}")
    print(f"content={response.choices[0].message.content}")

    return dict(temp = kws.get("temperature"),finish_reason=response.choices[0].finish_reason,total_tokens=response.usage.total_tokens,content={response.choices[0].message.content})

cases = [
    ("1",dict(temperature=0)),
    ("2",dict(temperature=0.7)),
    ("3",dict(temperature=1.3)),
    ("4",dict(max_tokens=20)),
]

with open("lessons/w1/out/day02_params.md", "w", encoding="utf-8") as f:
        f.write("| 组别 ｜ 参数 ｜ 输出 ｜ finishi_reason | tokens \n")
        f.write("----------------------------------------------\n")

for label,kw in cases:
    result = run(label,**kw)
    print(result)
    with open("lessons/w1/out/day02_params.md", "a", encoding="utf-8") as f:
        f.write(f'| {label} ｜ {result["temp"]} ｜ {result["content"]} ｜ {result["finish_reason"]} | {result["total_tokens"]} \n')






