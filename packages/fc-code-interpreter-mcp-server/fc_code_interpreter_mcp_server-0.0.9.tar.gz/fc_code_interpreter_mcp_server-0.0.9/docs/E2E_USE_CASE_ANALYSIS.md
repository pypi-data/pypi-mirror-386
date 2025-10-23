# 端到端用例分析

## 用户需求

用户希望通过 MCP Server 实现以下端到端流程：

### 第一轮执行
1. 启动一个 code interpreter session
2. 创建一个上下文（context）
3. 基于该上下文执行代码
4. 获取代码执行结果

### 第二轮执行（两种选择）
**选项 A：复用现有资源**
- 复用之前的 session 和 context ID
- 继续在同一上下文中执行代码（状态持久化）

**选项 B：创建新资源**
- 创建新的 session
- 创建新的 context
- 在新环境中执行代码

---

## 当前设计分析

### ❌ 问题 1：Session 管理不透明

**当前设计：**
```python
# 服务器启动时自动创建
session_info = await agentrun_manager.create_session()
default_session_id = session_info.session_id
```

**问题：**
- Session 在服务器启动时自动创建，用户**无法通过 MCP 工具控制**
- 用户**无法获取** session ID
- 用户**无法创建**新的 session
- 用户**无法复用**指定的 session

**影响：**
- ❌ 用户无法主动启动 session
- ❌ 用户无法在第二轮中复用或创建新 session
- ❌ 不满足端到端需求的第一步和第二轮选项 B

---

### ❌ 问题 2：run_code 工具缺少必要参数

**当前设计：**
```json
{
  "name": "run_code",
  "arguments": {
    "code": "print('Hello')"
  }
}
```

**问题：**
- `run_code` 工具**没有 context_id 参数**
- 文档中提到 "使用 context_id 参数"，但工具定义中**缺失**该参数
- 用户无法指定在哪个上下文中执行代码

**影响：**
- ❌ 用户无法在自己创建的上下文中执行代码
- ❌ `create_context` 工具返回的 context_id 无法使用
- ❌ 不满足端到端需求的第 3 步

---

### ⚠️ 问题 3：Context 与 Session 的关系不清晰

**当前设计：**
- `create_context` 工具只需要 `name` 参数
- 没有明确 context 属于哪个 session

**问题：**
- Context 应该属于某个 session，但当前设计中没有关联
- 如果用户创建新 session，之前的 context 是否还能用？
- Session 之间的 context 如何隔离？

**影响：**
- ⚠️ 资源管理逻辑不清晰
- ⚠️ 可能导致跨 session 的 context 冲突

---

## 预期设计（应该是什么样）

### 工具 1：`create_session` - 创建会话 🆕

```json
{
  "name": "create_session",
  "description": "创建一个新的代码解释器会话",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "会话名称（可选）"
      },
      "timeout": {
        "type": "integer",
        "description": "会话超时时间（秒）（可选，默认 3600）"
      }
    },
    "required": []
  }
}
```

**输出：**
```json
{
  "session_id": "sess-abc123",
  "interpreter_id": "ci-xyz789",
  "status": "active",
  "created_at": "2025-10-22T07:00:00Z",
  "message": "会话创建成功"
}
```

---

### 工具 2：`create_context` - 创建上下文（需要改进）

**当前定义：**
```json
{
  "name": "create_context",
  "arguments": {
    "name": "user-alice"
  }
}
```

**应该改为：**
```json
{
  "name": "create_context",
  "arguments": {
    "session_id": "sess-abc123",  // 🆕 必需参数
    "name": "user-alice",
    "description": "Alice 的工作环境"
  }
}
```

**理由：**
- Context 必须明确属于某个 session
- 支持在不同 session 中创建同名 context

---

### 工具 3：`run_code` - 执行代码（需要改进）

**当前定义：**
```json
{
  "name": "run_code",
  "arguments": {
    "code": "print('Hello')"
  }
}
```

**应该改为：**
```json
{
  "name": "run_code",
  "arguments": {
    "code": "print('Hello')",
    "session_id": "sess-abc123",   // 🆕 可选参数（默认使用 default session）
    "context_id": "ctx-xyz789"     // 🆕 可选参数（默认使用 default context）
  }
}
```

**理由：**
- 支持在指定 session 和 context 中执行
- 向后兼容：如果不提供，使用默认值
- 满足用户复用 session 和 context 的需求

---

## 完整端到端流程演示

### 场景 1：首次使用（使用默认 session）

```json
// 步骤 1: 创建上下文（使用默认 session）
{
  "name": "create_context",
  "arguments": {
    "name": "my-analysis"
  }
}
// 响应: {"context_id": "ctx-111", "session_id": "default", ...}

// 步骤 2: 在该上下文中执行代码
{
  "name": "run_code",
  "arguments": {
    "code": "x = 42",
    "context_id": "ctx-111"
  }
}
// 响应: {"stdout": "", "success": true}

// 步骤 3: 继续在同一上下文执行
{
  "name": "run_code",
  "arguments": {
    "code": "print(x)",
    "context_id": "ctx-111"
  }
}
// 响应: {"stdout": "42\n", "success": true}
```

---

### 场景 2：显式创建 session 和 context

```json
// 步骤 1: 创建新会话
{
  "name": "create_session",
  "arguments": {
    "name": "alice-session"
  }
}
// 响应: {"session_id": "sess-abc123", ...}

// 步骤 2: 在新会话中创建上下文
{
  "name": "create_context",
  "arguments": {
    "session_id": "sess-abc123",
    "name": "my-context"
  }
}
// 响应: {"context_id": "ctx-xyz789", "session_id": "sess-abc123", ...}

// 步骤 3: 在指定 session 和 context 中执行代码
{
  "name": "run_code",
  "arguments": {
    "code": "data = [1, 2, 3]",
    "session_id": "sess-abc123",
    "context_id": "ctx-xyz789"
  }
}
// 响应: {"stdout": "", "success": true}

// 步骤 4: 第二轮 - 复用 session 和 context
{
  "name": "run_code",
  "arguments": {
    "code": "print(sum(data))",
    "session_id": "sess-abc123",
    "context_id": "ctx-xyz789"
  }
}
// 响应: {"stdout": "6\n", "success": true}
```

---

### 场景 3：在第二轮创建新 session

```json
// 第一轮已完成，现在第二轮...

// 步骤 1: 创建新的 session
{
  "name": "create_session",
  "arguments": {
    "name": "new-session"
  }
}
// 响应: {"session_id": "sess-new456", ...}

// 步骤 2: 在新 session 中创建 context
{
  "name": "create_context",
  "arguments": {
    "session_id": "sess-new456",
    "name": "fresh-context"
  }
}
// 响应: {"context_id": "ctx-fresh999", ...}

// 步骤 3: 在新环境中执行（之前的变量不存在）
{
  "name": "run_code",
  "arguments": {
    "code": "print('New environment')",
    "session_id": "sess-new456",
    "context_id": "ctx-fresh999"
  }
}
// 响应: {"stdout": "New environment\n", "success": true}
```

---

## 架构调整建议

### 调整 1：添加 `create_session` 工具

**实现要点：**
```python
@app.list_tools()
async def list_tools():
    return [
        Tool(name="create_session", ...),
        Tool(name="create_context", ...),
        Tool(name="run_code", ...),
        Tool(name="health_check", ...)
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "create_session":
        session_info = await agentrun_manager.create_session(
            session_id=arguments.get("name")
        )
        return format_session_response(session_info)
```

---

### 调整 2：更新 `create_context` 工具

**添加 session_id 参数：**
```python
class CreateContextSchema(BaseModel):
    session_id: Optional[str] = None  # 可选，默认使用 default session
    name: str
    description: Optional[str] = None

# 在数据面创建 context 时关联 session
context = await data_client.create_context(
    code_interpreter_id=interpreter_id,
    session_id=session_id or default_session_id,
    name=arguments.name,
    ...
)
```

---

### 调整 3：更新 `run_code` 工具

**添加 session_id 和 context_id 参数：**
```python
class RunCodeSchema(BaseModel):
    code: str
    session_id: Optional[str] = None  # 可选，默认使用 default
    context_id: Optional[str] = None  # 可选，默认使用 default

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "run_code":
        result = await data_client.execute_code(
            code_interpreter_id=agentrun_manager.interpreter_id,
            session_id=arguments.session_id or default_session_id,
            code=arguments.code,
            context_id=arguments.context_id or "default",
            ...
        )
```

---

## 总结

### 当前设计的问题

| 需求 | 当前状态 | 是否满足 |
|------|----------|---------|
| 启动 code interpreter session | ❌ 无工具，自动创建 | ❌ 否 |
| 创建上下文 | ✅ `create_context` 工具存在 | ⚠️ 部分（缺少 session 关联） |
| 基于上下文执行代码 | ❌ `run_code` 缺少 `context_id` 参数 | ❌ 否 |
| 获取执行结果 | ✅ 返回 stdout/stderr | ✅ 是 |
| 第二轮复用 session/context | ❌ 无法指定 session/context | ❌ 否 |
| 第二轮创建新 session/context | ❌ 无法创建新 session | ❌ 否 |

**结论：当前设计 ❌ 无法满足用户的端到端需求。**

---

### 需要的改进

1. **🆕 添加 `create_session` 工具**
   - 允许用户显式创建和管理 session
   - 返回 session_id 供后续使用

2. **🔧 修改 `create_context` 工具**
   - 添加 `session_id` 参数（可选）
   - 明确 context 与 session 的关联关系

3. **🔧 修改 `run_code` 工具**
   - 添加 `session_id` 参数（可选）
   - 添加 `context_id` 参数（可选）
   - 支持在指定 session 和 context 中执行

4. **📝 更新文档**
   - 添加完整的端到端用例说明
   - 更新工具 API 规范
   - 添加 session 生命周期管理说明

---

## 向后兼容性

为了保持向后兼容，建议：

1. **默认行为**：如果不提供 session_id/context_id，使用默认值
2. **渐进式采用**：用户可以选择使用简单模式（默认）或完全控制模式
3. **文档说明**：在文档中清楚说明简单模式和高级模式的区别

### 简单模式（向后兼容）
```json
// 不需要管理 session，使用默认值
{"name": "run_code", "arguments": {"code": "print('Hello')"}}
```

### 高级模式（完全控制）
```json
// 完全控制 session 和 context
{
  "name": "run_code",
  "arguments": {
    "code": "print('Hello')",
    "session_id": "sess-123",
    "context_id": "ctx-456"
  }
}
```

---

## 优先级建议

### P0（必须）
- ✅ 添加 `create_session` 工具
- ✅ 更新 `run_code` 工具（添加 context_id 参数）

### P1（重要）
- ✅ 更新 `create_context` 工具（添加 session_id 参数）
- ✅ 更新 TOOLS_API.md 文档

### P2（可选）
- 添加 `list_sessions` 工具（列出所有 session）
- 添加 `list_contexts` 工具（列出 session 中的所有 context）
- 添加 `delete_session` 工具（提前删除 session）
- 添加 `delete_context` 工具（删除指定 context）
