# 快速启动指南

## ⚡ 3 步启动

### 1. 启动 Sandbox Docker

```bash
# 启动本地 sandbox
docker-compose up -d

# 验证服务运行
curl http://localhost:5001/health
```

**预期输出**: `{"status":"healthy"}`

### 2. 启动 MCP 服务器

```bash
# 方式 A: 使用 Make (推荐)
make run

# 方式 B: 使用 UV 直接运行
uv run sandbox-mcp-server

# 方式 C: 指定配置
SANDBOX_URL=http://localhost:5001 MCP_PORT=3000 uv run sandbox-mcp-server
```

### 3. 测试连接

```bash
# 使用 MCP Inspector (自动启动)
make debug

# 或手动启动 Inspector
npx @modelcontextprotocol/inspector http://localhost:3000/sse
```

## 📊 预期输出

服务器启动后显示:

```
============================================================
Code Interpreter MCP Server Starting...
============================================================
INFO:sandbox-mcp-server:Initializing E2B Sandbox...
INFO:sandbox-mcp-server:Using code interpreter endpoint: http://localhost:5001
INFO:sandbox-mcp-server:✅ E2B Sandbox initialized successfully
INFO:sandbox-mcp-server:   Sandbox ID: sandbox-xxxxxxxx
INFO:sandbox-mcp-server:   Endpoint: http://localhost:5001
INFO:sandbox-mcp-server:Server initialization complete
INFO:sandbox-mcp-server:Supported languages: Python, JavaScript
INFO:sandbox-mcp-server:Available tools: 4 (run_code, create_context, stop_context, list_contexts)
INFO:sandbox-mcp-server:Mode: E2B Sandbox
============================================================
INFO:sandbox-mcp-server:Starting SSE server on 0.0.0.0:3000
INFO:sandbox-mcp-server:SSE endpoint: http://0.0.0.0:3000/sse
INFO:sandbox-mcp-server:Message endpoint: http://0.0.0.0:3000/messages
INFO:     Uvicorn running on http://0.0.0.0:3000
```

## 🔧 配置

环境变量 (可选):

```bash
# Sandbox 配置
export SANDBOX_URL=http://localhost:5001  # 本地 sandbox 地址

# MCP 服务器配置
export MCP_HOST=0.0.0.0                   # 监听地址
export MCP_PORT=3000                      # 服务端口
export LOG_LEVEL=INFO                     # 日志级别

# AgentRun 云服务 (可选)
export AGENTRUN_ACCESS_KEY_ID=your_key
export AGENTRUN_ACCESS_KEY_SECRET=your_secret
export AGENTRUN_ACCOUNT_ID=your_account
export AGENTRUN_REGION=cn-hangzhou
```

## ✅ 验证

在 MCP Inspector 中测试工具:

### 1. 创建 Context
工具: `create_context`
```json
{
  "name": "test-python",
  "language": "python",
  "description": "Test Python context"
}
```

**预期响应**:
```json
{
  "context_id": "ctx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "test-python",
  "language": "python",
  "status": "active",
  "message": "Python context created successfully"
}
```

### 2. 运行代码
工具: `run_code`
```json
{
  "context_id": "ctx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "code": "x = 100\nprint(f'Value: {x}')\nprint(f'Square: {x**2}')"
}
```

**预期响应**:
```json
{
  "stdout": "Value: 100\nSquare: 10000\n",
  "stderr": "",
  "success": true,
  "execution_time": 0.123,
  "error": null
}
```

### 3. 列出所有 Contexts
工具: `list_contexts`
```json
{}
```

### 4. 停止 Context
工具: `stop_context`
```json
{
  "context_id": "ctx-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

## 🐛 故障排查

### 端口被占用
```bash
# 查看端口占用
lsof -i :3000

# 使用其他端口
MCP_PORT=3001 make run
```

### Sandbox 未运行
```bash
# 检查容器状态
docker ps | grep sandbox

# 启动 sandbox
docker-compose up -d

# 查看日志
docker-compose logs sandbox
```

### 依赖安装错误
```bash
# 重新安装依赖
uv install

# 或使用 pip
pip install -e .
```

### 代码执行错误
```bash
# 查看服务器日志
tail -f /tmp/mcp-server.log

# 检查 sandbox 健康状态
curl http://localhost:5001/health
```

## 📚 更多文档

- [README.md](README.md) - 项目总览
- [README_SSE.md](README_SSE.md) - SSE 详细文档
- [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) - Make 命令指南
- [WARP.md](WARP.md) - WARP AI 开发指南
- [docs/TOOLS_API.md](docs/TOOLS_API.md) - API 参考文档

---

**就这么简单！🎉**
