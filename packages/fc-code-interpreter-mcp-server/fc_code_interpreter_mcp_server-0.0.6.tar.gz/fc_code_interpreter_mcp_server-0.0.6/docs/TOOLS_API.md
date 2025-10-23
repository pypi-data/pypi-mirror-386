# MCP 服务器工具 API 规范

## 概述

本文档定义了 AgentRun MCP 服务器暴露的工具。该服务器实现了模型上下文协议（MCP），通过 AgentRun 的安全沙箱环境提供代码执行能力。

**服务器名称**：`agentrun-mcp-server`  
**协议**：MCP via stdio  
**传输方式**：标准输入/输出（stdio）

---

## 工具列表

当前实现的工具：**4 个**  
计划中的工具：**3 个**  
内部功能：**健康检查（自动执行，非 MCP 工具）**

---

## 当前实现的工具

### 1. `run_code` - 执行 Python 代码

在安全、隔离的 AgentRun 沙箱环境中执行 Python 代码。Session 自动从池中分配，同一 context_id 中保持状态持久化。

**重要**：必须先使用 `create_context` 创建 context，才能执行代码。

#### 工具元数据

```json
{
  "name": "run_code",
  "description": "在 AgentRun 的安全沙箱中运行 Python 代码。必须指定 context_id。Session 自动从池分配。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "description": "要执行的 Python 代码"
      },
      "context_id": {
        "type": "string",
        "description": "执行上下文 ID（必填），使用 create_context 创建"
      }
    },
    "required": ["code", "context_id"]
  }
}
```

#### 输入参数

| 参数 | 类型 | 必需 | 描述 |
|-----------|------|----------|-------------|
| `code` | string | **是** | 在沙箱中执行的 Python 代码 |
| `context_id` | string | **是** | 执行上下文 ID，必须通过 `create_context` 创建 |

#### 输入示例

**示例 1：基本执行**
```json
{
  "code": "import numpy as np\nx = np.array([1, 2, 3, 4, 5])\nprint(f'Mean: {x.mean()}')\nprint(f'Sum: {x.sum()}')",
  "context_id": "ctx-abc123"  // 必须指定
}
```

**示例 2：多次执行（同一 context）**
```json
{
  "code": "x = 100\nprint(x)",
  "context_id": "ctx-abc123"  // 必须指定
}
```

#### 输出格式

工具返回包含执行结果的 JSON 对象：

```typescript
{
  stdout: string;      // 代码执行的标准输出
  stderr: string;      // 标准错误输出
  success: boolean;    // 执行是否成功
  execution_time?: number;  // 执行时间（秒）（可选）
}
```

#### 输出示例

**成功案例：**
```json
{
  "stdout": "Mean: 3.0\nSum: 15\n",
  "stderr": "",
  "success": true,
  "execution_time": 0.123
}
```

**错误案例：**
```json
{
  "stdout": "",
  "stderr": "Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nNameError: name 'undefined_variable' is not defined\n",
  "success": false,
  "execution_time": 0.012
}
```

#### 行为详情

##### 状态持久化
变量和导入在同一 context_id 的多次调用中保持：

```python
# 前提：先创建 context
# create_context(name="user-bob") → context_id = "ctx-bob123"

# 第一次调用
code = "x = 42"
context_id = "ctx-bob123"
# 结果: success=true, stdout=""

# 第二次调用（同一 context_id）
code = "print(x)"
context_id = "ctx-bob123"
# 结果: success=true, stdout="42\n"

# 第三次调用（不同 context_id）
# create_context(name="user-alice") → context_id = "ctx-alice456"
code = "print(x)"
context_id = "ctx-alice456"
# 结果: NameError - x 未定义（ctx-alice456 的 context 中没有 x）
```

**Session 自动管理**：
- Session 从池中自动分配，用户无需关心
- 同一 context_id 的代码在所有 Session 中保持一致状态
- Session 有效期 60 分钟，过期后自动重建新 Session
- Context 状态独立于 Session，Session 重建不影响 Context 数据

**重要**：
- ⚠️ 执行代码前必须先创建 context
- ⚠️ context_id 是必填参数，不可省略
- ⚠️ 使用不存在的 context_id 会返回错误

##### 执行上下文
- **语言**：Python 3.10+
- **语法**：Jupyter Notebook 风格（支持脚本和 REPL 模式）
- **超时**：30 秒（可配置）
- **内存**：从解释器实例共享（默认 2048MB）
- **CPU**：从解释器实例共享（默认 2.0 核心）

##### 支持的特性
- ✅ 标准 Python 库
- ✅ 常见数据科学库（numpy、pandas、matplotlib 等）
- ✅ 跨调用的变量持久化
- ✅ 导入语句缓存
- ✅ 多行代码块
- ✅ 打印和日志输出捕获
- ✅ 错误回溯捕获

##### 限制
- ⚠️ 执行超时：30 秒
- ⚠️ 无文件系统持久化（临时存储）
- ⚠️ 无网络访问（PUBLIC 网络模式）
- ⚠️ Session 池大小固定为 3，并发执行可能需要等待可用 Session
- ⚠️ 大量输出可能被截断

#### 错误处理

##### 客户端错误（4xx 等效）
- **无效输入**：缺少或无效的 `code` 或 `context_id` 参数
  ```json
  {
    "error": "Invalid arguments: code and context_id are required",
    "code": "INVALID_PARAMS"
  }
  ```

- **Context 不存在**：指定的 context_id 不存在
  ```json
  {
    "error": "Context not found: ctx-abc123",
    "code": "CONTEXT_NOT_FOUND"
  }
  ```

##### 服务器错误（5xx 等效）
- **服务器未就绪**：解释器未初始化
  ```json
  {
    "error": "AgentRun manager not initialized or not ready",
    "code": "SERVER_NOT_READY"
  }
  ```

- **执行失败**：网络或 API 错误
  ```json
  {
    "stdout": "",
    "stderr": "HTTP Error: 500\nInternal Server Error",
    "success": false
  }
  ```

#### 使用示例

##### 示例 1：简单计算
```json
{
  "name": "run_code",
  "arguments": {
    "code": "result = 2 + 2\nprint(f'2 + 2 = {result}')"
  }
}
```

**响应：**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"stdout\": \"2 + 2 = 4\\n\",\n  \"stderr\": \"\",\n  \"success\": true\n}"
    }
  ]
}
```

##### 示例 2：数据分析
```json
{
  "name": "run_code",
  "arguments": {
    "code": "import pandas as pd\ndata = {'name': ['Alice', 'Bob', 'Charlie'], 'age': [25, 30, 35]}\ndf = pd.DataFrame(data)\nprint(df.describe())"
  }
}
```

##### 示例 3：错误处理
```json
{
  "name": "run_code",
  "arguments": {
    "code": "x = 1 / 0"
  }
}
```

**响应：**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"stdout\": \"\",\n  \"stderr\": \"Traceback (most recent call last):\\n  File \\\"<stdin>\\\", line 1, in <module>\\nZeroDivisionError: division by zero\\n\",\n  \"success\": false\n}"
    }
  ]
}
```

##### 示例 4：状态持久化
```json
// 第一个请求
{
  "name": "run_code",
  "arguments": {
    "code": "counter = 0\nfor i in range(5):\n    counter += i\nprint(f'Counter: {counter}')"
  }
}

// 第二个请求（同一会话）
{
  "name": "run_code",
  "arguments": {
    "code": "counter += 10\nprint(f'Counter now: {counter}')"
  }
}
```

#### 性能特征

- **首次调用延迟**：约 50-100ms（热解释器）
- **后续调用**：约 20-50ms（缓存上下文）
- **超时**：30 秒（执行）
- **并发性**：串行化（每个会话一次执行一个）

#### 安全考虑

##### 沙箱隔离
- 代码在隔离的 AgentRun 容器中运行
- 无法访问主机文件系统
- 网络访问由配置控制
- 强制执行资源限制（CPU、内存、时间）

##### 数据隐私
- 执行后不持久化代码
- 会话结束时清除变量
- 日志不永久存储

##### 最佳实践
- ⚠️ 不要在未审查的情况下执行不受信任的代码
- ⚠️ 避免在变量中存储敏感数据
- ⚠️ 注意并发场景中的共享状态
- ⚠️ 如果暴露给多个用户，实施速率限制

---

---

## 2. `create_context` - 创建执行上下文

创建一个新的隔离执行上下文，用于在同一解释器实例中隔离不同用户或不同任务的代码执行环境。

**支持语言**：Python 和 JavaScript。

**重要**：在执行 `run_code` 之前必须先创建 context。


### 工具元数据

```json
{
  "name": "create_context",
  "description": "创建一个新的隔离代码执行上下文，支持 Python 和 JavaScript",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "上下文名称，用于标识和管理上下文"
      },
      "language": {
        "type": "string",
        "enum": ["python", "javascript"],
        "description": "编程语言，可选值: python (默认) 或 javascript"
      },
      "description": {
        "type": "string",
        "description": "上下文描述信息（可选）"
      }
    },
    "required": ["name"]
  }
}
```

### 输入参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | **是** | 上下文名称，建议使用有意义的名称如 "user-123", "task-data-analysis" |
| `language` | string | 否 | 编程语言，可选值: `"python"` (默认) 或 `"javascript"` |
| `description` | string | 否 | 上下文的描述信息，便于管理和调试 |

### 输入示例

**示例 1：Python Context（默认）**
```json
{
  "name": "user-alice-session",
  "description": "Alice 的数据分析会话"
  // language 不指定，默认 python
}
```

**示例 2：Python Context（显式指定）**
```json
{
  "name": "data-analysis-task",
  "language": "python",
  "description": "使用 pandas 进行数据分析"
}
```

**示例 3：JavaScript Context**
```json
{
  "name": "web-scraping-task",
  "language": "javascript",
  "description": "网页数据爬取和处理"
}
```

### 输出格式

工具返回包含创建的上下文信息的 JSON 对象：

```typescript
{
  context_id: string;  // 上下文唯一标识符
  name: string;  // 上下文名称
  language: "python" | "javascript";  // 编程语言
  description: string;  // 上下文描述
  created_at: string;  // 创建时间 (ISO 8601 格式)
  status: string;  // 上下文状态 (active)
  message: string;  // 创建结果描述
}
```

### 输出示例

**Python Context（默认）：**
```json
{
  "context_id": "ctx-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "user-alice-session",
  "language": "python",
  "description": "Alice 的数据分析会话",
  "created_at": "2025-10-22T06:53:42Z",
  "status": "active",
  "message": "Python context created successfully"
}
```

**JavaScript Context：**
```json
{
  "context_id": "ctx-b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "name": "web-scraping-task",
  "language": "javascript",
  "description": "网页数据爬取和处理",
  "created_at": "2025-10-22T06:55:00Z",
  "status": "active",
  "message": "JavaScript context created successfully"
}
```

### 行为详情

#### 上下文隔离

每个上下文都是独立的执行环境：

```python
# 在 context-A 中
run_code(code="x = 100", context_id="context-A")
# 结果: x = 100 in context-A

# 在 context-B 中
run_code(code="print(x)", context_id="context-B")
# 结果: NameError - x 未定义（context-B 中没有 x）

# 再次在 context-A 中
run_code(code="print(x)", context_id="context-A")
# 结果: 100（context-A 中的 x 仍然存在）
```

#### 上下文命名规范

推荐的命名模式：
- **用户会话**：`user-{user_id}` 或 `user-{username}-session`
- **任务隔离**：`task-{task_name}` 或 `job-{job_id}`
- **临时测试**：`temp-{timestamp}` 或 `test-{test_name}`
- **功能模块**：`module-{module_name}`

#### 生命周期

- **创建**：通过 `create_context` 工具创建
- **使用**：在 `run_code` 中通过 `context_id` 参数使用
- **持久化**：在会话期间持续存在
- **清理**：会话结束时自动清理所有上下文

### 使用场景

#### 1. Python 数据分析
```python
# 创建 Python Context
ctx = create_context(
    name="data-analysis",
    language="python",
    description="pandas 数据分析任务"
)["context_id"]

# 执行 Python 代码
run_code(
    code="""
import pandas as pd
df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
print(df.sum())
""",
    context_id=ctx
)
```

#### 2. JavaScript 网页处理
```python
# 创建 JavaScript Context
ctx = create_context(
    name="web-processing",
    language="javascript",
    description="网页数据处理"
)["context_id"]

# 执行 JavaScript 代码
run_code(
    code="""
const data = {name: 'Alice', age: 25};
console.log(JSON.stringify(data));
""",
    context_id=ctx
)
```

#### 3. 混合使用
```python
# Python Context 用于数据处理
py_ctx = create_context(name="data-processing", language="python")["context_id"]
run_code(code="data = [1,2,3,4,5]\nresult = sum(data)", context_id=py_ctx)

# JavaScript Context 用于前端逻辑
js_ctx = create_context(name="frontend-logic", language="javascript")["context_id"]
run_code(code="const items = [1,2,3]; console.log(items.length);", context_id=js_ctx)

# 清理
stop_context(context_id=py_ctx)
stop_context(context_id=js_ctx)
```

#### 4. 多用户隔离
```python
# 用户 A 使用 Python
user_a_ctx = create_context(name="user-alice", language="python")["context_id"]
run_code(code="x = 100", context_id=user_a_ctx)

# 用户 B 使用 JavaScript
user_b_ctx = create_context(name="user-bob", language="javascript")["context_id"]
run_code(code="let x = 200;", context_id=user_b_ctx)

# 两个用户的 x 变量完全隔离
```

### 使用示例

#### 示例 1：创建用户上下文

```json
{
  "name": "create_context",
  "arguments": {
    "name": "user-bob",
    "description": "Bob 的工作环境"
  }
}
```

**响应：**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"context_id\": \"ctx-b2c3d4e5-f6a7-8901-bcde-f12345678901\",\n  \"name\": \"user-bob\",\n  \"description\": \"Bob 的工作环境\",\n  \"language\": \"python\",\n  \"created_at\": \"2025-10-22T06:53:42Z\",\n  \"status\": \"active\",\n  \"message\": \"上下文创建成功\"\n}"
    }
  ]
}
```

#### 示例 2：在新上下文中执行代码

```json
// 步骤 1: 创建上下文
{
  "name": "create_context",
  "arguments": {
    "name": "data-analysis-1"
  }
}

// 步骤 2: 在该上下文中执行代码
{
  "name": "run_code",
  "arguments": {
    "code": "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})\nprint(df.sum())",
    "context_id": "data-analysis-1"
  }
}
```

#### 示例 3：多上下文并行工作

```json
// 创建上下文 A
{"name": "create_context", "arguments": {"name": "context-a"}}

// 创建上下文 B
{"name": "create_context", "arguments": {"name": "context-b"}}

// 在 A 中设置变量
{"name": "run_code", "arguments": {"code": "result = 'A'", "context_id": "context-a"}}

// 在 B 中设置变量
{"name": "run_code", "arguments": {"code": "result = 'B'", "context_id": "context-b"}}

// 在 A 中读取（得到 'A'）
{"name": "run_code", "arguments": {"code": "print(result)", "context_id": "context-a"}}

// 在 B 中读取（得到 'B'）
{"name": "run_code", "arguments": {"code": "print(result)", "context_id": "context-b"}}
```

### 错误处理

#### 无效上下文名称
```json
{
  "error": "Invalid context name: name cannot be empty or contain special characters",
  "code": "INVALID_CONTEXT_NAME"
}
```

#### 不支持的语言
```json
{
  "error": "Unsupported language: ruby. Must be 'python' or 'javascript'",
  "code": "INVALID_LANGUAGE"
}
```

#### 上下文创建失败
```json
{
  "error": "Failed to create context: internal server error",
  "code": "CONTEXT_CREATION_FAILED"
}
```

### 性能特征

- **创建延迟**：< 100ms
- **内存开销**：每个上下文约 10-50MB（取决于加载的库）
- **并发限制**：建议单个解释器实例不超过 50 个活跃上下文
- **生命周期**：与会话生命周期相同

### 最佳实践

1. **命名规范**
   - 使用有意义的名称
   - 包含用户/任务标识符
   - 避免使用特殊字符

2. **上下文管理**
   - 为每个用户创建独立上下文
   - 不同任务使用不同上下文
   - 避免在 default 上下文中执行用户代码

3. **资源控制**
   - 监控活跃上下文数量
   - 避免创建过多上下文
   - 长期不用的上下文考虑清理（未来功能）

4. **错误隔离**
   - 一个上下文的错误不影响其他上下文
   - 使用上下文隔离不同用户的执行

---

## 3. `stop_context` - 停止执行上下文

停止并清理指定的执行上下文，释放相关资源。

### 工具元数据

```json
{
  "name": "stop_context",
  "description": "停止并清理指定的执行上下文，释放相关资源",
  "inputSchema": {
    "type": "object",
    "properties": {
      "context_id": {
        "type": "string",
        "description": "要停止的上下文 ID"
      }
    },
    "required": ["context_id"]
  }
}
```

### 输入参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|​------|
| `context_id` | string | **是** | 要停止的上下文 ID |

### 输入示例

```json
{
  "context_id": "ctx-abc123"
}
```

### 输出格式

```typescript
{
  context_id: string;  // 被停止的上下文 ID
  status: "stopped";   // 状态
  message: string;     // 描述信息
}
```

### 输出示例

**成功停止：**
```json
{
  "context_id": "ctx-abc123",
  "status": "stopped",
  "message": "Context stopped successfully"
}
```

**错误示例：Context 不存在**
```json
{
  "error": "Context not found: ctx-abc123",
  "code": "CONTEXT_NOT_FOUND"
}
```

### 行为详情

#### 正常停止流程

1. **验证 Context 存在**
   - 检查 context_id 是否在注册表中
   - 如果不存在，返回 `CONTEXT_NOT_FOUND` 错误

2. **等待正在运行的代码完成**
   - 如果有代码正在此 Context 中执行，等待其完成
   - 不会强制中断正在执行的代码

3. **调用 AgentRun 底层 API**
   - 调用 AgentRun 的 `stop_context` API
   - 清理底层变量空间

4. **从注册表删除**
   - 从内存的 `context_registry` 中删除
   - 释放相关资源

5. **返回成功状态**

#### 错误处理

| 错误情况 | 错误码 | 处理方式 |
|----------|------|----------|
| Context 不存在 | `CONTEXT_NOT_FOUND` | 返回友好错误信息 |
| Context 正在使用 | 无（等待） | 等待执行完成后停止 |
| AgentRun API 失败 | `STOP_FAILED` | 返回底层错误信息 |

### 使用场景

1. **任务完成后清理**
   ```python
   # 完成数据分析任务
   stop_context(context_id="ctx-data-analysis")
   ```

2. **用户会话结束**
   ```python
   # 用户登出或会话超时
   stop_context(context_id="ctx-user-alice-session")
   ```

3. **资源管理**
   ```python
   # 定期清理不活跃的 Context
   contexts = list_contexts()
   for ctx in contexts["contexts"]:
       if is_inactive(ctx):
           stop_context(context_id=ctx["context_id"])
   ```

4. **错误恢复**
   ```python
   # 发生错误后清理 Context 重新开始
   try:
       run_code(code="...", context_id="ctx-task")
   except Exception:
       stop_context(context_id="ctx-task")
       # 重新创建
       new_ctx = create_context(name="task-retry")
   ```

### 使用示例

```json
{
  "name": "stop_context",
  "arguments": {
    "context_id": "ctx-abc123"
  }
}
```

**响应：**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"context_id\": \"ctx-abc123\",\n  \"status\": \"stopped\",\n  \"message\": \"Context stopped successfully\"\n}"
    }
  ]
}
```

### 性能特征

- **响应时间**：< 100ms（如果没有正在执行的代码）
- **阻塞时间**：最多 30 秒（等待正在执行的代码完成）
- **并发安全**：线程安全，可以并发调用

### 注意事项

- ⚠️ **停止后不可恢复**：Context 停止后无法重启，需要重新创建
- ⚠️ **数据丢失**：Context 中的所有变量和状态将被清理
- ⚠️ **引用无效**：停止后使用该 context_id 会返回 `CONTEXT_NOT_FOUND` 错误

---

## 4. `list_contexts` - 列出所有上下文

列出当前所有活跃的执行上下文。

### 工具元数据

```json
{
  "name": "list_contexts",
  "description": "列出当前所有活跃的执行上下文",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### 输入参数

无需输入参数。

### 输出格式

```typescript
{
  contexts: Array<{
    context_id: string;      // 上下文 ID
    name: string;            // 上下文名称
    description: string;     // 上下文描述
    language: string;        // 编程语言 (python)
    status: string;          // 状态 (active)
    created_at: string;      // 创建时间 (ISO 8601)
    last_used: string;       // 最后使用时间 (ISO 8601)
  }>;
  total: number;  // 总数
}
```

### 输出示例

**有多个 Context：**
```json
{
  "contexts": [
    {
      "context_id": "ctx-abc123",
      "name": "user-alice-session",
      "description": "Alice 的数据分析会话",
      "language": "python",
      "status": "active",
      "created_at": "2025-10-22T08:00:00Z",
      "last_used": "2025-10-22T09:05:00Z"
    },
    {
      "context_id": "ctx-def456",
      "name": "user-bob-session",
      "description": "Bob 的机器学习实验",
      "language": "python",
      "status": "active",
      "created_at": "2025-10-22T08:30:00Z",
      "last_used": "2025-10-22T09:00:00Z"
    }
  ],
  "total": 2
}
```

**没有 Context：**
```json
{
  "contexts": [],
  "total": 0
}
```

### 行为详情

#### 返回内容

- 返回当前所有 `active` 状态的 Context
- 按创建时间排序（最新的在前）
- 包含完整的 Context 元数据

#### 时间戳格式

- 所有时间字段使用 ISO 8601 格式
- 示例：`2025-10-22T09:05:00Z`
- 时区：UTC

### 使用场景

1. **监控 Context 使用情况**
   ```python
   contexts = list_contexts()
   print(f"当前有 {contexts['total']} 个活跃 Context")
   ```

2. **查找特定 Context**
   ```python
   contexts = list_contexts()
   for ctx in contexts["contexts"]:
       if ctx["name"] == "user-alice-session":
           print(f"Found: {ctx['context_id']}")
   ```

3. **清理不活跃 Context**
   ```python
   contexts = list_contexts()
   now = datetime.now()
   for ctx in contexts["contexts"]:
       last_used = datetime.fromisoformat(ctx["last_used"])
       if (now - last_used).total_seconds() > 3600:  # 1小时不活跃
           stop_context(context_id=ctx["context_id"])
   ```

4. **调试和故障诊断**
   ```python
   # 查看所有 Context 状态
   contexts = list_contexts()
   for ctx in contexts["contexts"]:
       print(f"{ctx['name']}: {ctx['status']} (last used: {ctx['last_used']})")
   ```

### 使用示例

```json
{
  "name": "list_contexts",
  "arguments": {}
}
```

**响应：**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"contexts\": [\n    {\n      \"context_id\": \"ctx-abc123\",\n      \"name\": \"user-alice-session\",\n      \"description\": \"Alice 的数据分析会话\",\n      \"language\": \"python\",\n      \"status\": \"active\",\n      \"created_at\": \"2025-10-22T08:00:00Z\",\n      \"last_used\": \"2025-10-22T09:05:00Z\"\n    }\n  ],\n  \"total\": 1\n}"
    }
  ]
}
```

### 性能特征

- **响应时间**：< 10ms（内存读取）
- **无副作用**：只读操作，不影响 Context 状态
- **可频繁调用**：适合用于监控和调试

### 注意事项

- ✅ 只显示活跃的 Context，已停止的不会显示
- ✅ `last_used` 时间在每次 `run_code` 后更新
- ✅ 返回结果为快照，可能与实际状态有短暂延迟

---

## 内部健康检查

服务器在启动后会**自动执行内部健康检查**，这不是一个 MCP 工具，而是服务器的内部功能。

### 自动健康检查流程

```
1. Code Interpreter 创建完成
   ↓
2. Session 池初始化完成（3 个 Session）
   ↓
3. 自动执行健康检查
   ├─ 验证 Interpreter 状态 = READY
   ├─ 验证 Session 池大小 = 3
   ├─ 验证所有 Session 可用
   └─ 记录健康状态到日志
   ↓
4. 服务器就绪，开始接受请求
```

### 健康检查内容

服务器内部会检查以下指标：

```typescript
{
  interpreter_ready: boolean,          // Interpreter 是否就绪
  interpreter_status: "READY" | ...,   // Interpreter 状态
  session_pool_size: number,           // Session 池大小
  session_pool_available: number,      // 可用 Session 数量
  all_sessions_healthy: boolean,       // 所有 Session 是否健康
  startup_time_seconds: number         // 启动耗时
}
```

### 日志输出示例

```
[INFO] AgentRun 初始化开始...
[INFO] 创建 Code Interpreter: ci-abc123def456
[INFO] 等待 Interpreter 就绪...
[INFO] Interpreter 状态: READY
[INFO] 初始化 Session 池 (大小: 3)...
[INFO] Session-1 创建成功: session-a1b2c3
[INFO] Session-2 创建成功: session-d4e5f6
[INFO] Session-3 创建成功: session-g7h8i9
[INFO] 执行健康检查...
[INFO] ✓ Interpreter 就绪
[INFO] ✓ Session 池健康 (3/3 可用)
[INFO] ✓ 所有 Session 验证通过
[INFO] 服务器启动完成，耗时: 65 秒
[INFO] MCP Server 就绪，等待请求...
```

### 故障处理

如果健康检查失败，服务器会：
1. 记录详细错误日志
2. 尝试重建失败的 Session
3. 如果无法恢复，服务器启动失败并退出

---

## 未来工具（计划中）

### 3. `upload_file` - 上传文件到沙箱
将文件上传到沙箱以供代码执行使用。

**状态**：计划中  
**优先级**：中

### 4. `download_file` - 从沙箱下载文件
从沙箱下载生成的文件。

**状态**：计划中  
**优先级**：中

### 5. `list_files` - 列出沙箱文件
列出沙箱文件系统中的文件。

**状态**：计划中  
**优先级**：低

---

## 工具发现

客户端可以使用 MCP `tools/list` 请求发现可用工具：

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "run_code",
        "description": "在 AgentRun 的安全沙箱中运行 Python 代码。使用 Jupyter Notebook 语法。状态在同一会话中保持。",
        "inputSchema": {
          "type": "object",
          "properties": {
            "code": {
              "type": "string",
              "description": "要执行的 Python 代码"
            }
          },
          "required": ["code"]
        }
      },
      {
        "name": "create_context",
        "description": "创建一个新的隔离代码执行上下文，支持 Python 和 JavaScript",
        "inputSchema": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "上下文名称"
            },
            "language": {
              "type": "string",
              "enum": ["python", "javascript"],
              "description": "编程语言，python (默认) 或 javascript"
            },
            "description": {
              "type": "string",
              "description": "上下文描述（可选）"
            }
          },
          "required": ["name"]
        }
      },
      {
        "name": "stop_context",
        "description": "停止并清理指定的执行上下文，释放相关资源",
        "inputSchema": {
          "type": "object",
          "properties": {
            "context_id": {
              "type": "string",
              "description": "要停止的上下文 ID"
            }
          },
          "required": ["context_id"]
        }
      },
      {
        "name": "list_contexts",
        "description": "列出当前所有活跃的执行上下文",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      }
    ]
  }
}
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|---------|------|---------|
| 1.0.0 | 2025-10-22 | 初始版本，包含 `run_code` 工具 |
| 0.1.0 | 2025-10-15 | 基于 E2B 的实现 |

---

## 参考资料

- [模型上下文协议规范](https://spec.modelcontextprotocol.io/)
- [AgentRun 文档](packages/python/agentrun-ci-sdk-preview/sdk/README.md)
- [实施计划](./IMPLEMENTATION_PLAN_CN.md)

---

## 附录：与 E2B 的对比

### 工具接口兼容性

AgentRun MCP 服务器与 E2B 版本保持接口兼容：

| 特性 | E2B | AgentRun |
|------|-----|----------|
| **工具名称** | `run_code` | `run_code` ✅ |
| **输入参数** | `{code: string}` | `{code: string}` ✅ |
| **输出格式** | `{stdout, stderr}` | `{stdout, stderr, success, execution_time}` ✅+ |
| **状态持久化** | ❌ 无 | ✅ 支持 |
| **启动时间** | 即时 | 约 60 秒（一次性） |
| **执行延迟** | 2-5 秒 | 20-100ms |

### 迁移注意事项

从 E2B 迁移到 AgentRun 时，现有的 MCP 客户端代码无需修改，因为工具接口保持兼容。主要区别：

1. **服务器启动**：需要等待约 60 秒完成解释器初始化
2. **状态管理**：变量现在在会话中持久化
3. **性能提升**：后续调用更快（20-50ms vs 2-5秒）
4. **错误格式**：增加了 `success` 和 `execution_time` 字段

### 兼容性示例

**E2B 客户端代码（无需修改）：**
```typescript
const result = await client.callTool({
  name: "run_code",
  arguments: {
    code: "print('Hello World')"
  }
});

const output = JSON.parse(result.content[0].text);
console.log(output.stdout);  // 在两个实现中都有效
```
