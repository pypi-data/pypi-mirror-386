# E2B 到 AgentRun 迁移指南

## 当前 E2B 实现（Python）

### 架构概述

当前 E2B MCP 服务器实现流程：

```
MCP 客户端（Claude Desktop）
    ↓（stdio）
MCP 服务器（mcp_server/server.py）
    ↓
E2B 沙箱（e2b_code_interpreter）
    ↓
在 E2B 云中执行代码
```

### 关键组件

#### 1. **MCP 服务器**（`mcp_server/server.py`）
- **服务器初始化**：创建名为 `"e2b-code-mcp-server"` 的 MCP 服务器
- **工具注册**：通过 `@app.list_tools()` 装饰器注册 `run_code` 工具
- **工具执行**：通过 `@app.call_tool()` 装饰器处理代码执行
- **通信**：通过 `mcp.server.stdio.stdio_server` 使用 stdio 传输

#### 2. **E2B 集成**
```python
from e2b_code_interpreter import Sandbox

# 简单实例化
sbx = Sandbox()

# 执行代码
execution = sbx.run_code(code)

# 访问结果
execution.logs.stdout  # 标准输出
execution.logs.stderr  # 错误输出
```

#### 3. **数据流**

1. **输入验证**：使用 Pydantic `ToolSchema` 验证输入
   ```python
   class ToolSchema(BaseModel):
       code: str
   ```

2. **执行**：每次请求创建新的 Sandbox 实例
   ```python
   sbx = Sandbox()
   execution = sbx.run_code(arguments.code)
   ```

3. **输出格式化**：返回 JSON 格式的日志
   ```python
   result = {
       "stdout": execution.logs.stdout,
       "stderr": execution.logs.stderr,
   }
   return [TextContent(type="text", text=json.dumps(result, indent=2))]
   ```

### 当前局限性

- **无状态**：每次执行都创建新的 Sandbox 实例
- **无上下文**：无法在代码执行之间保持状态
- **简单认证**：仅需要 `E2B_API_KEY` 环境变量

---

## AgentRun 实现

### 架构概述

AgentRun 使用双层架构，控制面和数据面分离：

```
MCP 客户端（Claude Desktop）
    ↓（stdio）
MCP 服务器（mcp_server/server.py）
    ↓
AgentRun CodeInterpreter 客户端
    ├── 控制面客户端（创建/管理解释器）
    │   ↓
    │   AgentRun 控制 API（agentrun.cn-hangzhou.aliyuncs.com）
    │
    └── 数据面客户端（执行代码）
        ↓
        AgentRun 数据 API（{tenant_id}.agentrun-data.{region}.aliyuncs.com）
```

### 关键组件

#### 1. **控制面**（`control_plane.py`）
使用 `alibabacloud-agentrun20250910` SDK 管理解释器生命周期：

- **创建解释器**：提供计算资源
  ```python
  create_request = CreateCodeInterpreterRequest(
      body=CreateCodeInterpreterInput(
          code_interpreter_name="my-interpreter",
          cpu=2.0,
          memory=2048,
          network_configuration=NetworkConfiguration(network_mode="PUBLIC"),
          session_idle_timeout_seconds=3600,
      )
  )
  response = client.create_code_interpreter(create_request)
  ```

- **获取状态**：监控解释器就绪状态
  ```python
  status_response = client.get_code_interpreter(code_interpreter_id)
  # 等待状态为 "READY" 或 "RUNNING"
  ```

- **会话管理**：创建和管理会话
  ```python
  session = client.start_session(code_interpreter_id, session_request)
  ```

#### 2. **数据面**（`data_plane.py`）
使用 HTTP API 执行代码：

- **基础 URL**：`https://{tenant_id}.agentrun-data.{region}.aliyuncs.com`
- **端点**：`/api/v1/code_interpreters/{id}/sessions/{session_id}/code`

- **执行代码**：
  ```python
  response = data_client.execute_code(
      code_interpreter_id=interpreter_id,
      code="print('Hello')",
      context_id="default",
      execution_timeout=30
  )
  ```

- **上下文管理**：在调用之间维护执行上下文
  ```python
  context = data_client.create_context(
      code_interpreter_id=interpreter_id,
      name="my-context",
      language="python"
  )
  ```

#### 3. **统一客户端**（`code_interpreter.py`）
组合两个平面的高级 API：

```python
interpreter = CodeInterpreter(
    access_key_id="...",
    access_key_secret="...",
    region="cn-hangzhou"
)

# 创建解释器实例
instance = interpreter.create_interpreter(
    name="my-interpreter",
    cpu=2.0,
    memory=2048
)

# 启动会话
session = interpreter.start_session()

# 使用上下文执行代码
result = interpreter.execute_code(
    code="print('Hello')",
    context_id="default"
)
```

### 认证

AgentRun 需要：
1. **Access Key ID**：`AGENTRUN_ACCESS_KEY_ID`
2. **Access Key Secret**：`AGENTRUN_ACCESS_KEY_SECRET`
3. **Account ID**：`AGENTRUN_ACCOUNT_ID`（租户路由必需）
4. **Region**：`AGENTRUN_REGION`（默认：`cn-hangzhou`）

### 与 E2B 的主要差异

| 特性 | E2B | AgentRun |
|---------|-----|----------|
| **架构** | 单层（直接 SDK） | 双层（控制面 + 数据面） |
| **实例创建** | 自动/隐式 | 显式（通过控制面） |
| **会话** | 无会话概念 | 需要会话管理 |
| **上下文** | 无状态 | 有状态的上下文管理 |
| **认证** | 仅 API 密钥 | Access Key + Secret + Account ID |
| **租户路由** | 不需要 | 数据面需要租户 ID |
| **资源管理** | 自动 | 手动（创建/启动/停止/删除） |

---

## 迁移步骤

### 第一阶段：理解当前流程

1. **当前 E2B 流程**：
   ```
   客户端请求 → MCP 服务器 → 创建沙箱 → 执行代码 → 返回结果
   ```

2. **每个请求都是独立的** - 不维护状态

### 第二阶段：设计 AgentRun 集成

#### 选项 A：无状态（类似 E2B）
每次请求创建和销毁解释器：
```
客户端请求 → MCP 服务器 
    → 创建解释器（控制面）
    → 等待 READY
    → 启动会话
    → 执行代码（数据面）
    → 删除解释器
    → 返回结果
```

**优点**：简单，隔离执行
**缺点**：慢（创建开销），昂贵

#### 选项 B：会话池（推荐用于生产）
维护长期存在的解释器：
```
服务器启动 → 创建 N 个解释器 → 启动会话 → 保持活跃

客户端请求 → MCP 服务器
    → 从池中获取解释器
    → 执行代码（数据面）
    → 将解释器返回池中
    → 返回结果

服务器关闭 → 清理解释器
```

**优点**：快速，高效，维护上下文
**缺点**：更复杂，需要生命周期管理

#### 选项 C：单例解释器（推荐用于开始）
单个共享解释器：
```
服务器启动 → 创建解释器 → 启动会话

客户端请求 → MCP 服务器
    → 使用唯一 context_id 执行代码
    → 返回结果

服务器关闭 → 删除解释器
```

**优点**：简单性和效率的平衡
**缺点**：共享状态可能导致冲突

### 第三阶段：实施任务

1. **更新依赖项**
   ```toml
   [tool.poetry.dependencies]
   # 移除 e2b-code-interpreter
   # 添加 AgentRun SDK
   agentrun-code-interpreter = "^0.1.0"
   alibabacloud-agentrun20250910 = "^1.0.0"
   ```

2. **更新环境配置**
   ```python
   # 旧配置（E2B）
   E2B_API_KEY = os.getenv("E2B_API_KEY")
   
   # 新配置（AgentRun）
   AGENTRUN_ACCESS_KEY_ID = os.getenv("AGENTRUN_ACCESS_KEY_ID")
   AGENTRUN_ACCESS_KEY_SECRET = os.getenv("AGENTRUN_ACCESS_KEY_SECRET")
   AGENTRUN_ACCOUNT_ID = os.getenv("AGENTRUN_ACCOUNT_ID")
   AGENTRUN_REGION = os.getenv("AGENTRUN_REGION", "cn-hangzhou")
   ```

3. **初始化 AgentRun 客户端**
   ```python
   from agentrun_code_interpreter import CodeInterpreter
   
   # 创建单例解释器（服务器启动时）
   interpreter = CodeInterpreter(
       access_key_id=AGENTRUN_ACCESS_KEY_ID,
       access_key_secret=AGENTRUN_ACCESS_KEY_SECRET,
       region=AGENTRUN_REGION
   )
   
   # 创建并等待解释器
   instance = interpreter.create_interpreter(
       name="mcp-server-interpreter",
       cpu=2.0,
       memory=2048,
       network_mode=NetworkMode.PUBLIC,
       session_timeout=3600
   )
   
   # 启动会话
   session = interpreter.start_session()
   ```

4. **更新工具执行**
   ```python
   @app.call_tool()
   async def call_tool(name: str, arguments: Any):
       if name != "run_code":
           raise ValueError(f"Unknown tool: {name}")
       
       arguments = ToolSchema.model_validate(arguments)
       
       # 旧方式（E2B）
       # sbx = Sandbox()
       # execution = sbx.run_code(arguments.code)
       
       # 新方式（AgentRun）
       result = interpreter.execute_code(
           code=arguments.code,
           context_id="default",  # 或为每个用户生成唯一上下文
           execution_timeout=30
       )
       
       return [
           TextContent(
               type="text",
               text=json.dumps({
                   "stdout": result.stdout,
                   "stderr": result.stderr
               }, indent=2)
           )
       ]
   ```

5. **添加生命周期管理**
   ```python
   async def startup():
       """服务器启动时初始化解释器"""
       global interpreter
       # 创建并启动解释器
       
   async def shutdown():
       """服务器关闭时清理解释器"""
       if interpreter and interpreter.code_interpreter_id:
           interpreter.control_client.delete_code_interpreter(
               interpreter.code_interpreter_id
           )
   
   async def main():
       await startup()
       try:
           async with stdio_server() as (read_stream, write_stream):
               await app.run(read_stream, write_stream, app.create_initialization_options())
       finally:
           await shutdown()
   ```

### 第四阶段：测试

1. **环境设置**
   ```bash
   export AGENTRUN_ACCESS_KEY_ID="your_key"
   export AGENTRUN_ACCESS_KEY_SECRET="your_secret"
   export AGENTRUN_ACCOUNT_ID="your_account"
   export AGENTRUN_REGION="cn-hangzhou"
   ```

2. **使用 MCP Inspector 测试**
   ```bash
   npx @modelcontextprotocol/inspector \
     uv \
     --directory packages/python \
     run \
     e2b-mcp-server
   ```

3. **验证功能**
   - 解释器创建
   - 会话管理
   - 代码执行
   - 错误处理
   - 关闭时清理

### 第五阶段：优化

1. **添加上下文隔离**用于并发请求
2. **实施连接池**（如果需要）
3. **添加重试逻辑**处理瞬态故障
4. **监控资源使用**并调整 CPU/内存
5. **添加日志记录**用于调试和监控

---

## 代码对比

### E2B 版本（当前）
```python
from e2b_code_interpreter import Sandbox

sbx = Sandbox()
execution = sbx.run_code(code)
result = {
    "stdout": execution.logs.stdout,
    "stderr": execution.logs.stderr,
}
```

### AgentRun 版本（迁移目标）
```python
from agentrun_code_interpreter import CodeInterpreter

# 一次性设置
interpreter = CodeInterpreter(...)
interpreter.create_interpreter(...)
interpreter.start_session()

# 每次请求执行
result = interpreter.execute_code(code)
output = {
    "stdout": result.stdout,
    "stderr": result.stderr,
}
```

---

## 建议

1. **从选项 C（单例）开始**以简化
2. **添加适当的错误处理**处理网络问题
3. **实施优雅关闭**以清理资源
4. **考虑连接超时**基于代码复杂性
5. **添加指标/日志**以监控性能
6. **部署前用真实的 Claude Desktop 测试**

---

## 其他资源

- AgentRun SDK README：`packages/python/agentrun-ci-sdk-preview/sdk/README.md`
- 示例实现：`packages/python/agentrun-ci-sdk-preview/example/advanced_demo.py`
- SDK 文档：查看 INSTALLATION.md 了解详细设置
