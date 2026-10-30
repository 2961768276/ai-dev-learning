#!/usr/bin/env bash
# 构建镜像并起服务。用法：./scripts/build.sh   或  TAG=kb-api:dev ./scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TAG="${TAG:-kb-api:0.1}"

docker build -t "$TAG" .
docker image ls "$TAG"

if [[ -f docker-compose.yml ]]; then
  docker compose up -d --build
  echo "已启动：http://127.0.0.1:8000/health"
fi
