#!/bin/bash

# 快速启动 SSE MCP 服务器
# 使用方法: ./start_server.sh [port]

PORT=${1:-3000}

echo "============================================"
echo "启动 SSE MCP 服务器"
echo "============================================"
echo ""

# 设置环境变量
export SANDBOX_BASE_URL="${SANDBOX_BASE_URL:-http://localhost:8080}"
export MCP_HOST="${MCP_HOST:-0.0.0.0}"
export MCP_PORT="$PORT"
export SESSION_POOL_SIZE="${SESSION_POOL_SIZE:-3}"
export SESSION_LIFETIME_HOURS="${SESSION_LIFETIME_HOURS:-6}"

echo "配置:"
echo "  Sandbox URL: $SANDBOX_BASE_URL"
echo "  MCP Host: $MCP_HOST"
echo "  MCP Port: $MCP_PORT"
echo "  Session Pool: $SESSION_POOL_SIZE"
echo ""

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo "错误: uv 未安装"
    echo "请访问 https://docs.astral.sh/uv/getting-started/installation/ 安装 uv"
    exit 1
fi

# 启动服务器
echo "启动服务器..."
uv run python -m mcp_server
