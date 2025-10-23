# Server Implementation - server.py

## 概述

`server.py` 已根据最新设计完全重写，实现了 AgentRun MCP 服务器的完整架构。

**版本**: v2.2.0  
**日期**: 2025-10-22  
**状态**: 核心框架完成，待集成 AgentRun SDK

---

## 主要特性

### ✅ 已实现

1. **4 个 MCP 工具**
   - `run_code` - 执行 Python/JavaScript 代码（context_id 必填）
   - `create_context` - 创建上下文（支持 Python 和 JavaScript）
   - `stop_context` - 停止并清理上下文
   - `list_contexts` - 列出所有活跃上下文

2. **多语言支持**
   - Python（默认）
   - JavaScript
   - 语言验证和错误处理

3. **Context 管理**
   - 内存中的 `context_registry`
   - 自动生成 UUID 格式的 context_id
   - 跟踪 created_at 和 last_used 时间
   - 完整的 CRUD 操作

4. **数据模型**
   - `ContextInfo` - Context 信息数据类
   - `RunCodeSchema` - run_code 参数验证
   - `CreateContextSchema` - create_context 参数验证
   - `StopContextSchema` - stop_context 参数验证

5. **错误处理**
   - 统一的错误响应格式
   - Context 不存在错误 (CONTEXT_NOT_FOUND)
   - 无效语言错误 (INVALID_LANGUAGE)
   - 参数验证错误 (INVALID_PARAMS)
   - 执行失败错误 (EXECUTION_FAILED)

6. **生命周期管理**
   - `initialize_server()` - 服务器启动初始化
   - `cleanup_server()` - 服务器关闭清理
   - 优雅的启动和关闭日志

### 🚧 待实现（TODO）

以下功能已预留接口，等待 AgentRun SDK 集成：

1. **Session 池管理**
   ```python
   # TODO: lines 86-88
   agentrun_manager: Optional[AgentRunManager] = None
   ```

2. **代码执行**
   ```python
   # TODO: lines 189-198 (handle_run_code)
   # - Acquire session from pool
   # - Execute via AgentRun data plane API
   # - Release session back to pool
   ```

3. **Context API 调用**
   ```python
   # TODO: lines 245-250 (handle_create_context)
   # - Call AgentRun create_context API
   
   # TODO: lines 305-306 (handle_stop_context)
   # - Call AgentRun stop_context API
   ```

4. **服务器初始化**
   ```python
   # TODO: lines 370-383 (initialize_server)
   # - Load AgentRun configuration
   # - Initialize AgentRunManager with pool_size=3
   # - Perform health check
   ```

5. **服务器清理**
   ```python
   # TODO: lines 397-399 (cleanup_server)
   # - Cleanup AgentRun resources
   # - Stop all sessions
   # - Delete interpreter
   ```

---

## 代码结构

```
server.py (424 lines)
├── Module Docstring (1-8)
├── Imports (10-28)
├── Logging Setup (33-35)
│
├── Data Models (38-51)
│   └── ContextInfo
│
├── Tool Schemas (54-73)
│   ├── RunCodeSchema
│   ├── CreateContextSchema
│   └── StopContextSchema
│
├── Global State (76-88)
│   ├── context_registry
│   ├── server_start_time
│   └── agentrun_manager (TODO)
│
├── MCP Server (91-126)
│   ├── app = Server()
│   └── @app.list_tools()
│
├── Tool Router (129-162)
│   └── @app.call_tool()
│
├── Tool Handlers (165-357)
│   ├── handle_run_code() (169-222)
│   ├── handle_create_context() (225-285)
│   ├── handle_stop_context() (288-325)
│   └── handle_list_contexts() (328-357)
│
├── Server Lifecycle (360-405)
│   ├── initialize_server()
│   └── cleanup_server()
│
└── Main Entry Point (408-424)
    └── main()
```

---

## 工具详细说明

### 1. run_code

**功能**: 在指定 Context 中执行代码

**参数**:
```python
{
    "code": str,        # 必填
    "context_id": str   # 必填
}
```

**当前行为**:
- ✅ 验证参数
- ✅ 检查 context 是否存在
- ✅ 获取 context 语言信息
- ✅ 更新 last_used 时间
- 🚧 Mock 执行结果（待实现真实执行）

**返回**:
```json
{
  "stdout": "...",
  "stderr": "...",
  "success": true,
  "execution_time": 0.123
}
```

---

### 2. create_context

**功能**: 创建新的执行上下文

**参数**:
```python
{
    "name": str,                    # 必填
    "language": str = "python",     # 可选，默认 python
    "description": str = ""         # 可选
}
```

**当前行为**:
- ✅ 验证参数
- ✅ 验证语言（python 或 javascript）
- ✅ 生成 UUID 格式的 context_id
- ✅ 创建 ContextInfo 对象
- ✅ 注册到 context_registry
- 🚧 调用 AgentRun API（待实现）

**返回**:
```json
{
  "context_id": "ctx-uuid",
  "name": "...",
  "language": "python" | "javascript",
  "description": "...",
  "created_at": "2025-10-22T09:00:00Z",
  "status": "active",
  "message": "Python context created successfully"
}
```

---

### 3. stop_context

**功能**: 停止并清理上下文

**参数**:
```python
{
    "context_id": str  # 必填
}
```

**当前行为**:
- ✅ 验证参数
- ✅ 检查 context 是否存在
- ✅ 从 context_registry 删除
- 🚧 调用 AgentRun API（待实现）

**返回**:
```json
{
  "context_id": "ctx-uuid",
  "status": "stopped",
  "message": "Context stopped successfully"
}
```

---

### 4. list_contexts

**功能**: 列出所有活跃上下文

**参数**: 无

**当前行为**:
- ✅ 遍历 context_registry
- ✅ 构建上下文列表
- ✅ 按创建时间排序（最新在前）
- ✅ 返回总数统计

**返回**:
```json
{
  "contexts": [
    {
      "context_id": "ctx-uuid",
      "name": "...",
      "language": "python" | "javascript",
      "description": "...",
      "status": "active",
      "created_at": "2025-10-22T09:00:00Z",
      "last_used": "2025-10-22T09:05:00Z"
    }
  ],
  "total": 1
}
```

---

## 使用示例

### 测试当前实现

```bash
# 1. 安装依赖
cd packages/python
uv install

# 2. 运行服务器（MCP Inspector）
npx @modelcontextprotocol/inspector \
  uv \
  --directory . \
  run \
  agentrun-mcp-server

# 3. 在 Inspector 中测试工具
```

### 测试流程

```
1. create_context(name="test", language="python")
   → 返回 context_id

2. run_code(code="x = 100", context_id=<from_step_1>)
   → 返回 Mock 结果

3. list_contexts()
   → 显示刚创建的 context

4. stop_context(context_id=<from_step_1>)
   → 停止 context

5. list_contexts()
   → 确认 context 已删除
```

---

## 下一步集成

### 需要添加的文件

1. **agentrun_manager.py**
   - `AgentRunManager` 类
   - `InterpreterConfig` 数据类
   - `SessionInfo` 数据类
   - Session 池管理逻辑

2. **data_plane_client.py**
   - `DataPlaneClient` 类
   - `ExecutionResult` 数据类
   - HTTP 客户端封装

3. **.env.example**
   ```bash
   AGENTRUN_ACCESS_KEY_ID=your_key
   AGENTRUN_ACCESS_KEY_SECRET=your_secret
   AGENTRUN_ACCOUNT_ID=your_account
   AGENTRUN_REGION=cn-hangzhou
   ```

### 修改点

在 `server.py` 中搜索 `# TODO:` 找到所有待实现的集成点，共 5 处。

---

## 测试清单

### 当前可测试

- ✅ 服务器启动和关闭
- ✅ 工具列表正确返回
- ✅ create_context 创建 Python context
- ✅ create_context 创建 JavaScript context
- ✅ create_context 语言验证（拒绝 "ruby"）
- ✅ list_contexts 返回正确列表
- ✅ stop_context 删除 context
- ✅ stop_context 错误处理（context 不存在）
- ✅ run_code Context 不存在错误
- ✅ run_code Mock 执行

### 待 AgentRun 集成后测试

- ⏳ 真实代码执行
- ⏳ Session 池分配和释放
- ⏳ Context 在 AgentRun 中创建
- ⏳ Context 状态持久化
- ⏳ 多语言代码执行
- ⏳ Session 过期处理
- ⏳ 健康检查

---

## 错误代码

| 错误码 | 说明 |
|--------|------|
| `INVALID_PARAMS` | 参数验证失败 |
| `CONTEXT_NOT_FOUND` | Context 不存在 |
| `INVALID_LANGUAGE` | 不支持的语言 |
| `EXECUTION_FAILED` | 工具执行失败 |

---

## 日志输出

### 启动日志

```
============================================================
AgentRun MCP Server Starting...
============================================================
Server initialization complete
Supported languages: Python, JavaScript
Available tools: 4 (run_code, create_context, stop_context, list_contexts)
============================================================
```

### 运行日志

```
INFO:agentrun-mcp-server:Created python context: ctx-abc123 (name: test)
INFO:agentrun-mcp-server:Executing code in context ctx-abc123 (language: python)
INFO:agentrun-mcp-server:Stopped context: ctx-abc123 (name: test)
```

### 关闭日志

```
============================================================
AgentRun MCP Server Shutting Down...
============================================================
Server cleanup complete
============================================================
```

---

## 总结

### 完成度

- **核心框架**: 100%
- **工具实现**: 80% (Mock 执行)
- **AgentRun 集成**: 0% (待实现)

### 优势

- ✅ 清晰的代码结构
- ✅ 完整的错误处理
- ✅ 预留 AgentRun 集成点
- ✅ 符合最新设计文档
- ✅ 可独立测试工具逻辑

### 下一步

1. 实现 `agentrun_manager.py`
2. 实现 `data_plane_client.py`
3. 集成到 `server.py`
4. 端到端测试

---

**文档版本**: v1.0  
**作者**: AI Assistant  
**日期**: 2025-10-22
