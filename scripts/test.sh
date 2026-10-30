#!/usr/bin/env bash
# lint + 测试。用法：./scripts/test.sh   或  ./scripts/test.sh -k ask
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== ruff check =="
uv run ruff check src tests scripts

if compgen -G "tests/test_*.py" > /dev/null; then
  echo "== pytest =="
  uv run pytest -q "$@"
else
  echo "tests/ 里还没有 test_*.py，pytest 跳过（Day 47 起启用）"
fi
