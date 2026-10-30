#!/usr/bin/env bash
# 跑 RAG 评测（脚本本身在 Day 40 创建）。用法：./scripts/eval.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f scripts/eval_rag.py ]]; then
  echo "scripts/eval_rag.py 还不存在（Day 40 创建）。"
  echo "现在可以先跑冒烟测试：./scripts/smoke_test.sh"
  exit 1
fi

exec uv run python scripts/eval_rag.py "$@"
