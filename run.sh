#!/usr/bin/env bash
# 天工智梯 · 统一启动脚本
set -a
[ -f .env ] && . ./.env
set +a
exec streamlit run app.py --server.port 8501 --server.headless true
