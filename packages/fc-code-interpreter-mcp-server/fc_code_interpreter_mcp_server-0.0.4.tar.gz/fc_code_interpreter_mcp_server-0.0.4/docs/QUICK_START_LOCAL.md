# 本地 Sandbox MCP Server 快速启动指南

## 🚀 快速开始

### 前置条件

- Docker 和 Docker Compose
- Python 3.10+
- uv 包管理器

### 第一步: 启动 Sandbox 服务

```bash
# 在项目根目录
cd /path/to/sandbox-code-interpreter-mcp-server

# 启动 Docker 服务
docker-compose up -d

# 验证服务运行
curl http://localhost:8080/health
# 预期输出: OK
```

### 第二步: 安装依赖

```bash
# 安装 Python 依赖
uv sync

# 或使用 pip
pip install -e .
```

### 第三步: 配置环境变量

创建 `.env` 文件:

```bash
# 本地 Sandbox 配置
SANDBOX_BASE_URL=http://localhost:8080
SANDBOX_TIMEOUT=30
SESSION_POOL_SIZE=3
SESSION_LIFETIME_HOURS=6
LOG_LEVEL=INFO
```

### 第四步: 测试服务

使用 MCP Inspector 测试:

```bash
npx @modelcontextprotocol/inspector \
  uv \
  --directory . \
  run \
  python -m mcp_server.server_local
```

## 📋 测试流程

在 MCP Inspector 中测试以下操作:

### 1. 创建 Context

```json
{
  "name": "test-python",
  "language": "python",
  "description": "Test Python context"
}
```

**预期输出**:
```json
{
  "context_id": "ctx-xxx",
  "name": "test-python",
  "language": "python",
  "status": "active",
  "created_at": "2025-10-22T11:30:00Z",
  "message": "Python context created successfully"
}
```

### 2. 执行代码

```json
{
  "code": "x = 100\nprint(f'Value: {x}')",
  "context_id": "ctx-xxx"
}
```

**预期输出**:
```json
{
  "stdout": "Value: 100\n",
  "stderr": "",
  "success": true,
  "execution_time": 0.15
}
```

### 3. 验证状态保持

```json
{
  "code": "print(f'Previous value: {x}')",
  "context_id": "ctx-xxx"
}
```

**预期输出**:
```json
{
  "stdout": "Previous value: 100\n",
  "stderr": "",
  "success": true,
  "execution_time": 0.12
}
```

### 4. 列出所有 Context

无需参数，直接调用 `list_contexts`

**预期输出**:
```json
{
  "contexts": [
    {
      "context_id": "ctx-xxx",
      "name": "test-python",
      "language": "python",
      "description": "Test Python context",
      "status": "active",
      "created_at": "2025-10-22T11:30:00Z",
      "last_used": "2025-10-22T11:31:00Z"
    }
  ],
  "total": 1,
  "session_pool": {
    "total_sessions": 3,
    "active_sessions": 3,
    "queue_size": 3,
    "oldest_session_age_hours": 0.02,
    "session_lifetime_hours": 6
  }
}
```

### 5. 停止 Context

```json
{
  "context_id": "ctx-xxx"
}
```

**预期输出**:
```json
{
  "context_id": "ctx-xxx",
  "status": "stopped",
  "message": "Context stopped successfully"
}
```

## 🔍 核心特性

### Session 管理

- **Session Pool**: 预创建 3 个 session（可配置）
- **生命周期**: 6 小时（可配置）
- **自动清理**: 每 5 分钟检查并清理过期 session
- **透明使用**: Session ID 自动添加到 HTTP header `X-CI-SESSION-ID`

### Context 管理

- **独立隔离**: 每个 context 有独立的执行环境
- **状态保持**: 变量在同一 context 多次执行间保持
- **多语言支持**: Python 和 JavaScript
- **生命周期管理**: 创建、使用、停止

### 错误处理

```json
// Context 不存在
{
  "error": "Context not found: ctx-invalid",
  "code": "CONTEXT_NOT_FOUND"
}

// 不支持的语言
{
  "error": "Unsupported language: java. Must be 'python' or 'javascript'",
  "code": "INVALID_LANGUAGE"
}

// 执行失败
{
  "error": "...",
  "code": "EXECUTION_FAILED"
}
```

## 🛠️ 配置选项

### 命令行参数

```bash
python -m mcp_server.server_local \
  --base-url http://localhost:8080 \
  --timeout 30 \
  --pool-size 5 \
  --session-lifetime 12 \
  --log-level DEBUG
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SANDBOX_BASE_URL` | `http://localhost:8080` | Sandbox 服务地址 |
| `SANDBOX_TIMEOUT` | `30` | 请求超时时间(秒) |
| `SESSION_POOL_SIZE` | `3` | Session 池大小 |
| `SESSION_LIFETIME_HOURS` | `6` | Session 生命周期(小时) |
| `LOG_LEVEL` | `INFO` | 日志级别 |

## 📊 监控和调试

### 查看日志

```bash
# MCP Server 日志（stdout）
# 在 MCP Inspector 中查看

# Sandbox 容器日志
docker logs sandbox-code-interpreter

# 实时跟踪
docker logs -f sandbox-code-interpreter
```

### Session Pool 状态

在 `list_contexts` 响应中包含 session pool 统计信息:

```json
{
  "session_pool": {
    "total_sessions": 3,
    "active_sessions": 3,
    "queue_size": 2,
    "oldest_session_age_hours": 0.5,
    "session_lifetime_hours": 6
  }
}
```

### 常见问题

#### 1. 无法连接到 Sandbox

```bash
# 检查容器状态
docker ps | grep sandbox-code-interpreter

# 检查容器日志
docker logs sandbox-code-interpreter

# 重启容器
docker-compose restart
```

#### 2. Session 过期过快

```bash
# 增加 session 生命周期
export SESSION_LIFETIME_HOURS=12

# 或在 .env 中配置
SESSION_LIFETIME_HOURS=12
```

#### 3. 代码执行超时

```bash
# 增加请求超时
export SANDBOX_TIMEOUT=60

# 或在 .env 中配置
SANDBOX_TIMEOUT=60
```

## 🎯 与 AgentRun 的对比

| 特性 | AgentRun | Local Sandbox |
|------|----------|---------------|
| **启动时间** | ~60 秒 | **< 5 秒** |
| **Context 创建** | 2-3 秒 | **< 100ms** |
| **执行延迟** | 100-500ms | **< 50ms** |
| **成本** | 按使用计费 | **免费** |
| **网络依赖** | 需要公网 | **本地** |
| **隐私** | 云端 | **完全本地** |
| **Session Header** | 无 | `X-CI-SESSION-ID` |
| **Session 生命周期** | 60 分钟 | **6 小时** |

## 🔄 与 Claude Desktop 集成

在 Claude Desktop 配置中添加:

```json
{
  "mcpServers": {
    "sandbox": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/sandbox-code-interpreter-mcp-server",
        "run",
        "python",
        "-m",
        "mcp_server.server_local"
      ],
      "env": {
        "SANDBOX_BASE_URL": "http://localhost:8080",
        "SESSION_POOL_SIZE": "3",
        "SESSION_LIFETIME_HOURS": "6"
      }
    }
  }
}
```

## ✅ 验证清单

- [ ] Docker 容器正常运行 (`docker ps`)
- [ ] Health 检查通过 (`curl http://localhost:8080/health`)
- [ ] MCP Inspector 可以连接
- [ ] 创建 Context 成功
- [ ] 代码执行成功
- [ ] 状态在多次执行间保持
- [ ] Session pool 正常工作
- [ ] Context 删除成功

## 📚 相关文档

- [Session 管理器实现](../mcp_server/session_manager.py)
- [本地 Sandbox 客户端](../mcp_server/local_sandbox_client.py)
- [MCP Server 实现](../mcp_server/server_local.py)
- [Docker Compose 配置](../docker-compose.yml)

---

**Enjoy coding with local sandbox! 🎉**
