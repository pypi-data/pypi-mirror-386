#!/bin/bash

# 测试 SSE MCP 服务器
# 
# 使用方法: ./test_sse_server.sh

set -e

echo "=========================================="
echo "SSE MCP Server 测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}✗${NC} $1 未安装"
        return 1
    fi
}

# 测试步骤
echo "步骤 1: 检查依赖"
echo "------------------"
check_command docker
check_command curl
check_command python3
echo ""

echo "步骤 2: 检查 Docker 容器"
echo "------------------"
if docker ps | grep -q sandbox-code-interpreter; then
    echo -e "${GREEN}✓${NC} sandbox-code-interpreter 容器正在运行"
else
    echo -e "${YELLOW}⚠${NC} sandbox-code-interpreter 容器未运行"
    echo "   启动容器: docker-compose up -d"
fi
echo ""

echo "步骤 3: 测试 Sandbox 服务"
echo "------------------"
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Sandbox 服务健康检查通过"
else
    echo -e "${RED}✗${NC} Sandbox 服务不可用"
    echo "   请确保 Docker 容器正在运行"
fi
echo ""

echo "步骤 4: 检查 Python 模块"
echo "------------------"
cd /Users/chenquan/Workspace/fc/sandboxes/sandbox-code-interpreter-mcp-server
if python3 -c "import mcp" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} mcp 模块已安装"
else
    echo -e "${RED}✗${NC} mcp 模块未安装"
    echo "   安装依赖: uv sync 或 pip install mcp"
fi

if python3 -c "from mcp_server.local_sandbox_client import LocalSandboxClient" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} local_sandbox_client 模块可导入"
else
    echo -e "${YELLOW}⚠${NC} local_sandbox_client 模块导入失败"
fi

if python3 -c "from mcp_server.session_manager import SessionManager" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} session_manager 模块可导入"
else
    echo -e "${YELLOW}⚠${NC} session_manager 模块导入失败"
fi
echo ""

echo "步骤 5: 启动提示"
echo "------------------"
echo "启动 SSE 服务器:"
echo "  uv run python -m mcp_server"
echo ""
echo "或使用环境变量:"
echo "  MCP_PORT=3000 uv run python -m mcp_server"
echo ""
echo "测试 SSE 服务器:"
echo "  npx @modelcontextprotocol/inspector http://localhost:3000/sse"
echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
