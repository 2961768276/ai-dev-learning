#!/usr/bin/env bash
# 服务冒烟测试：health → chat → ask → search
# 用法：
#   ./scripts/smoke_test.sh
#   BASE_URL=http://127.0.0.1:8000 ./scripts/smoke_test.sh
# 任一检查失败 → 退出码非零（可直接用在 CI / 每日复盘里）。
set -uo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MAX_TIME="${MAX_TIME:-60}"
FAIL=0

say()  { printf '\n== %s ==\n' "$1"; }
pass() { printf '  [PASS] %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; FAIL=1; }

json_get() {
  python3 -c '
import json, sys
try:
    data = json.loads(sys.stdin.read())
    for key in sys.argv[1].strip(".").split("."):
        data = data[int(key)] if key.isdigit() else data[key]
    print(json.dumps(data, ensure_ascii=False) if isinstance(data, (dict, list)) else data)
except Exception as exc:  # 输出可读的错误，而不是整段 traceback
    print(f"<json_get error: {exc}>")
' "$1"
}

expect_eq() {
  if [[ "$2" == "$3" ]]; then pass "$1 = $3"; else bad "$1 期望 [$2] 实际 [$3]"; fi
}

expect_nonempty() {
  if [[ -n "${2:-}" && "$2" != \<* ]]; then pass "$1 非空（${#2} 字符）"; else bad "$1 为空或字段不存在 [$2]"; fi
}

say "0/4 服务可达性  $BASE_URL/health"
if ! health=$(curl -fsS --max-time "$MAX_TIME" "$BASE_URL/health"); then
  bad "连不上服务：先跑 ./scripts/dev.sh，或 docker compose up -d"
  printf '\n结果：FAIL（服务未启动）\n'
  exit 1
fi
expect_eq "status" "ok" "$(printf '%s' "$health" | json_get status)"

say "1/4 POST /chat"
chat_body='{"message":"用一句话解释什么是 RAG","max_tokens":128}'
if resp=$(curl -fsS --max-time "$MAX_TIME" -X POST "$BASE_URL/chat" \
            -H 'Content-Type: application/json' -d "$chat_body"); then
  expect_nonempty "answer" "$(printf '%s' "$resp" | json_get answer)"
  tokens=$(printf '%s' "$resp" | json_get usage.total_tokens)
  if [[ "$tokens" =~ ^[0-9]+$ ]] && (( tokens > 0 )); then
    pass "usage.total_tokens = $tokens"
  else
    bad "usage.total_tokens 缺失或为 0（实际 [$tokens]）"
  fi
else
  bad "POST /chat 失败（查 422 校验、.env 里的 Key、上游错误码）"
fi

say "2/4 POST /ask"
ask_body='{"question":"这个项目怎么做文档切分？","top_k":4}'
if resp=$(curl -fsS --max-time "$MAX_TIME" -X POST "$BASE_URL/ask" \
            -H 'Content-Type: application/json' -d "$ask_body"); then
  expect_nonempty "answer" "$(printf '%s' "$resp" | json_get answer)"
  n=$(printf '%s' "$resp" | python3 -c \
      'import json,sys; d=json.load(sys.stdin); print(len(d.get("sources") or []))' 2>/dev/null || echo "<json error>")
  if [[ "$n" =~ ^[0-9]+$ ]] && (( n > 0 )); then
    pass "sources 条数 = $n"
  else
    bad "sources 为空（先 POST /documents 入库，再问一个语料里有的问题）"
  fi
else
  bad "POST /ask 失败（查 lifespan 是否初始化了 Chroma、collection 是否为空）"
fi

say "3/4 GET /search"
if resp=$(curl -fsS -G --max-time "$MAX_TIME" "$BASE_URL/search" \
            --data-urlencode "q=文档切分" --data-urlencode "top_k=3"); then
  n=$(printf '%s' "$resp" | python3 -c \
      'import json,sys; d=json.load(sys.stdin); print(len(d.get("results") or []))' 2>/dev/null || echo "<json error>")
  if [[ "$n" =~ ^[0-9]+$ ]] && (( n > 0 )); then
    pass "results 条数 = $n"
  else
    bad "results 为空（检索链路或阈值有问题）"
  fi
else
  bad "GET /search 失败（检查 query 参数名 q / top_k）"
fi

say "4/4 GET /version"
if resp=$(curl -fsS --max-time "$MAX_TIME" "$BASE_URL/version"); then
  expect_nonempty "version" "$(printf '%s' "$resp" | json_get version)"
else
  bad "GET /version 失败"
fi

printf '\n'
if (( FAIL == 0 )); then
  printf '结果：全部通过\n'
else
  printf '结果：存在失败，逐条看上面的 [FAIL]\n'
fi
exit "$FAIL"
