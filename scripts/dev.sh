#!/usr/bin/env bash
# 本地开发服务器（带热重载）。用法：./scripts/dev.sh   或  PORT=8001 ./scripts/dev.sh
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run uvicorn ai_dev_learning.main:app \
  --reload --host 127.0.0.1 --port "${PORT:-8000}"
