# 从 AgentRun 到本地 Sandbox 迁移指南

## 📖 概述

本文档指导如何将 MCP 服务器从 **AgentRun 云服务**迁移到**本地 Docker 部署的 sandbox-code-interpreter**。

---

## 🔍 核心差异对比

### 架构差异

| 维度 | AgentRun | Local Sandbox |
|------|----------|---------------|
| **部署位置** | 阿里云 (agentrun.cn-hangzhou.aliyuncs.com) | **本地 Docker (localhost:8080)** |
| **启动时间** | ~60 秒 (控制面创建) | **< 5 秒 (容器启动)** |
| **认证方式** | AccessKey + Secret + 签名 | **无认证 / 可选 Basic Auth** |
| **网络依赖** | 需要公网访问 | **纯本地通信** |
| **成本** | 按使用计费 | **免费 (本地资源)** |
| **API 端点** | `/api/v1/code_interpreters/{id}/sessions/{sid}/code` | **`/api/v1/contexts/{id}/execute`** |

### API 映射关系

| 功能 | AgentRun API | Local Sandbox API |
|------|--------------|-------------------|
| **创建执行环境** | `create_code_interpreter()` + `start_session()` | **`POST /api/v1/contexts`** |
| **执行代码** | `POST /api/v1/.../code` | **`POST /api/v1/contexts/{id}/execute`** |
| **删除环境** | `delete_code_interpreter()` | **`DELETE /api/v1/contexts/{id}`** |
| **列出环境** | `list_code_interpreters()` | **`GET /api/v1/contexts`** |

---

## 🚀 迁移步骤

### 第一步: 启动本地 Sandbox 服务

#### 1.1 使用 Docker Compose

```bash
# 在 mcp-server 项目根目录
cd /path/to/sandbox-code-interpreter-mcp-server

# 启动 sandbox 服务
docker-compose up -d

# 检查服务状态
docker-compose ps
docker-compose logs -f sandbox-code-interpreter

# 验证服务可用
curl http://localhost:8080/health
# 预期输出: OK
```

#### 1.2 测试 API 连通性

```bash
# 创建测试上下文
curl -X POST http://localhost:8080/api/v1/contexts \
  -H "Content-Type: application/json" \
  -d '{
    "type": "jupyter",
    "language": "python",
    "session_name": "test-session",
    "working_dir": "/workspace"
  }'

# 预期输出:
# {
#   "context_id": "ctx-xxx",
#   "type": "jupyter",
#   "status": "active",
#   "created_at": "2025-10-22T11:30:00Z"
# }

# 执行测试代码
curl -X POST http://localhost:8080/api/v1/contexts/ctx-xxx/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from Local Sandbox\")",
    "timeout": 30
  }'

# 预期输出:
# {
#   "output": {
#     "stdout": "Hello from Local Sandbox\n",
#     "stderr": ""
#   },
#   "success": true,
#   "execution_time": 0.123
# }
```

---

### 第二步: 修改 MCP 服务器代码

#### 2.1 更新 `server.py`

需要修改以下部分：

##### **A. 更新导入和全局变量**

```python
# 旧代码 (AgentRun)
from .agentrun_manager import AgentRunManager, InterpreterConfig
from .data_plane_client import DataPlaneClient, ExecutionConfig

# 新代码 (Local Sandbox)
from .local_sandbox_client import LocalSandboxClient, LocalSandboxConfig

# 全局状态
local_sandbox_client: Optional[LocalSandboxClient] = None
```

##### **B. 更新初始化逻辑**

```python
# 旧代码 (AgentRun)
async def initialize_server(args=None):
    global agentrun_manager, data_client
    
    config = InterpreterConfig(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        account_id=account_id,
        region=region,
    )
    
    agentrun_manager = AgentRunManager(config, pool_size=pool_size)
    await agentrun_manager.initialize()  # 60秒启动

# 新代码 (Local Sandbox)
async def initialize_server(args=None):
    global local_sandbox_client
    
    config = LocalSandboxConfig(
        base_url=os.getenv("SANDBOX_BASE_URL", "http://localhost:8080"),
        timeout=30,
    )
    
    local_sandbox_client = LocalSandboxClient(config)  # 即时连接
```

##### **C. 更新执行逻辑**

```python
# 旧代码 (AgentRun)
async def handle_run_code(arguments: Any):
    session = await agentrun_manager.acquire_session()
    try:
        exec_result = data_client.execute_code(
            code=args.code,
            context_id=args.context_id,
            session_id=session.session_id
        )
    finally:
        await agentrun_manager.release_session(session.session_id)

# 新代码 (Local Sandbox)
async def handle_run_code(arguments: Any):
    # 检查 context 是否存在
    if args.context_id not in context_registry:
        return [TextContent(type="text", text=json.dumps({
            "error": "Context not found",
            "code": "CONTEXT_NOT_FOUND"
        }))]
    
    # 直接执行，无需会话管理
    result = local_sandbox_client.execute_code(
        context_id=args.context_id,
        code=args.code,
        timeout=30
    )
    
    return [TextContent(type="text", text=json.dumps({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "success": result.success,
        "execution_time": result.execution_time
    }, indent=2))]
```

##### **D. 更新上下文创建**

```python
# 旧代码 (AgentRun)
async def handle_create_context(arguments: Any):
    session = await agentrun_manager.acquire_session()
    try:
        agentrun_context = data_client.interpreter.data_client.create_context(
            code_interpreter_id=agentrun_manager.interpreter_id,
            name=args.name,
            language=args.language
        )
        context_id = agentrun_context.id
    finally:
        await agentrun_manager.release_session(session.session_id)

# 新代码 (Local Sandbox)
async def handle_create_context(arguments: Any):
    # 直接创建 context
    sandbox_context = local_sandbox_client.create_context(
        name=args.name,
        language=args.language,
        context_type="jupyter"
    )
    
    context_id = sandbox_context.context_id
```

---

### 第三步: 更新环境变量配置

#### 3.1 更新 `.env` 文件

```bash
# 旧配置 (AgentRun)
# AGENTRUN_ACCESS_KEY_ID=your_key
# AGENTRUN_ACCESS_KEY_SECRET=your_secret
# AGENTRUN_ACCOUNT_ID=your_account
# AGENTRUN_REGION=cn-hangzhou

# 新配置 (Local Sandbox)
SANDBOX_BASE_URL=http://localhost:8080
SANDBOX_TIMEOUT=30
```

#### 3.2 更新 `pyproject.toml`

```toml
[tool.poetry.dependencies]
python = "^3.10"
mcp = "^1.0.0"

# 移除 AgentRun 依赖
# agentrun-code-interpreter = "^0.1.0"
# alibabacloud-agentrun20250910 = "^1.0.0"

# 添加本地 sandbox 依赖
requests = "^2.31.0"
```

---

### 第四步: 测试迁移

#### 4.1 使用 MCP Inspector 测试

```bash
# 启动 MCP Inspector
npx @modelcontextprotocol/inspector \
  uv \
  --directory . \
  run \
  agentrun-mcp-server

# 测试流程:
# 1. create_context(name="test", language="python")
# 2. run_code(code="x = 100\nprint(x)", context_id="ctx-xxx")
# 3. list_contexts()
# 4. stop_context(context_id="ctx-xxx")
```

#### 4.2 验证功能

- ✅ **Context 创建**: 是否返回有效的 context_id
- ✅ **代码执行**: stdout/stderr 是否正确
- ✅ **状态保持**: 多次执行是否共享变量
- ✅ **错误处理**: 错误代码是否返回 stderr
- ✅ **Context 删除**: 删除后是否无法访问

---

## 📊 性能对比

| 指标 | AgentRun | Local Sandbox |
|------|----------|---------------|
| **初始启动时间** | ~60 秒 | **< 5 秒** |
| **Context 创建** | 2-3 秒 | **< 100ms** |
| **代码执行延迟** | 100-500ms | **< 50ms** |
| **网络开销** | 公网往返 | **无 (本地回环)** |
| **并发能力** | 受会话池限制 | **取决于本地资源** |

---

## 🔧 故障排查

### 问题 1: 无法连接到 sandbox 服务

```bash
# 检查容器状态
docker ps | grep sandbox-code-interpreter

# 查看日志
docker logs sandbox-code-interpreter

# 检查端口占用
lsof -i :8080

# 测试连通性
curl http://localhost:8080/health
```

### 问题 2: 代码执行超时

```python
# 增加超时时间
config = LocalSandboxConfig(
    base_url="http://localhost:8080",
    timeout=60  # 增加到 60 秒
)
```

### 问题 3: Context 创建失败

```bash
# 检查 sandbox 日志
docker logs sandbox-code-interpreter | grep ERROR

# 验证请求格式
curl -v -X POST http://localhost:8080/api/v1/contexts \
  -H "Content-Type: application/json" \
  -d '{"type": "jupyter", "language": "python", "session_name": "test"}'
```

---

## 🎯 迁移清单

- [ ] 启动本地 sandbox-code-interpreter Docker 容器
- [ ] 验证 sandbox API 可访问 (curl /health)
- [ ] 创建 `local_sandbox_client.py`
- [ ] 修改 `server.py` 中的初始化逻辑
- [ ] 修改 `server.py` 中的执行逻辑
- [ ] 更新 `.env` 配置文件
- [ ] 更新 `pyproject.toml` 依赖
- [ ] 运行 `uv sync` 安装依赖
- [ ] 使用 MCP Inspector 测试功能
- [ ] 验证所有 4 个工具正常工作
- [ ] 测试错误场景和边界情况

---

## 📚 参考资源

- [sandbox-code-interpreter API 文档](../sandbox-code-interpreter/README.md)
- [Docker Compose 配置](../docker-compose.yml)
- [本地客户端实现](../mcp_server/local_sandbox_client.py)
- [MCP Inspector 使用指南](https://github.com/modelcontextprotocol/inspector)

---

## ⚡ 优势总结

迁移到本地 sandbox 后的优势:

1. **🚀 性能提升**: 初始化从 60 秒降至 < 5 秒
2. **💰 零成本**: 无需云服务费用
3. **🔒 隐私保护**: 代码完全在本地执行
4. **🛠️ 易于调试**: 直接访问日志和容器
5. **🌐 离线可用**: 无需网络连接
6. **⚙️ 灵活配置**: 完全控制资源和配置
