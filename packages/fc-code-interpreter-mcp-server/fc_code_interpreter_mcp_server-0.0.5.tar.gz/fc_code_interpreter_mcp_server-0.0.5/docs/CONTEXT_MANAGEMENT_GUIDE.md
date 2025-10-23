# Context 管理完整指南

## 概述

AgentRun MCP 服务器要求**显式的 Context 管理**。用户必须先创建 Context，然后在执行代码时指定 context_id。

---

## 核心概念

### Context 是什么？

**Context（上下文）**是一个隔离的代码执行环境：
- 每个 Context 有唯一的 `context_id`
- 支持 **Python** 和 **JavaScript** 两种编程语言
- Context 中的变量、函数、导入等状态完全隔离
- 不同 Context 之间互不影响
- Context 在所有 Session 间共享状态

### 为什么需要 Context？

1. **多用户隔离**：不同用户的代码不会互相干扰
2. **任务隔离**：同一用户的不同任务可以分别管理
3. **状态管理**：明确的生命周期控制，避免状态混乱
4. **资源控制**：可以主动清理不再使用的 Context

---

## 工具列表

AgentRun MCP 服务器提供 **4 个 Context 管理工具**：

| 工具 | 用途 | context_id 参数 |
|------|------|----------------|
| `create_context` | 创建新的 Context | 输出 |
| `run_code` | 在指定 Context 执行代码 | **必填** |
| `stop_context` | 停止并清理 Context | **必填** |
| `list_contexts` | 列出所有活跃 Context | 无 |

---

## 完整工作流程

### 流程图

```
1. create_context(name="user-alice", language="python")
   ↓
   返回: context_id = "ctx-abc123", language = "python"
   ↓
2. run_code(code="x = 100", context_id="ctx-abc123")
   ↓
   执行成功，x 存储在 ctx-abc123 中
   ↓
3. run_code(code="print(x)", context_id="ctx-abc123")
   ↓
   输出: 100 (使用同一 context，变量持久化)
   ↓
4. stop_context(context_id="ctx-abc123")
   ↓
   Context 被清理，ctx-abc123 不可再使用
```

---

## 详细示例

### 示例 1：基本工作流程

```python
# 步骤 1: 创建 Context
response = create_context(
    name="my-first-task",
    description="我的第一个数据分析任务"
)
context_id = response["context_id"]  # "ctx-abc123"

# 步骤 2: 在 Context 中执行代码
run_code(
    code="import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})",
    context_id=context_id
)

# 步骤 3: 继续在同一 Context 中执行
run_code(
    code="print(df.sum())",  # df 仍然存在
    context_id=context_id
)
# 输出: a    6

# 步骤 4: 完成后清理
stop_context(context_id=context_id)
```

---

### 示例 2：多语言支持

```python
# Python Context
py_ctx = create_context(
    name="python-task",
    language="python",
    description="Python 数据分析"
)["context_id"]

run_code(
    code="""
import pandas as pd
df = pd.DataFrame({'a': [1,2,3]})
print(df.sum())
""",
    context_id=py_ctx
)
# 输出: a    6

# JavaScript Context
js_ctx = create_context(
    name="javascript-task",
    language="javascript",
    description="JavaScript 数据处理"
)["context_id"]

run_code(
    code="""
const data = {name: 'Alice', age: 25};
console.log(JSON.stringify(data));
""",
    context_id=js_ctx
)
# 输出: {"name":"Alice","age":25}

# 清理
stop_context(context_id=py_ctx)
stop_context(context_id=js_ctx)
```

---

### 示例 3：多用户隔离

```python
# 用户 Alice 使用 Python
alice_ctx = create_context(name="user-alice", language="python")["context_id"]
run_code(code="x = 'Alice'", context_id=alice_ctx)

# 用户 Bob 使用 JavaScript
bob_ctx = create_context(name="user-bob", language="javascript")["context_id"]
run_code(code="let x = 'Bob';", context_id=bob_ctx)

# Alice 读取自己的 x (Python)
run_code(code="print(x)", context_id=alice_ctx)
# 输出: Alice

# Bob 读取自己的 x (JavaScript)
run_code(code="console.log(x);", context_id=bob_ctx)
# 输出: Bob

# 清理
stop_context(context_id=alice_ctx)
stop_context(context_id=bob_ctx)
```

---

### 示例 4：任务隔离

```python
# 任务 1: 数据清洗
cleaning_ctx = create_context(
    name="data-cleaning-task",
    description="清洗原始数据"
)["context_id"]

run_code(
    code="""
import pandas as pd
raw_data = pd.read_csv('data.csv')
cleaned_data = raw_data.dropna()
""",
    context_id=cleaning_ctx
)

# 任务 2: 数据分析（独立环境）
analysis_ctx = create_context(
    name="data-analysis-task",
    description="分析处理后的数据"
)["context_id"]

run_code(
    code="""
import pandas as pd
# 这里的 cleaned_data 不存在（不同 Context）
# 需要重新加载数据
data = pd.read_csv('cleaned_data.csv')
result = data.describe()
print(result)
""",
    context_id=analysis_ctx
)

# 清理
stop_context(context_id=cleaning_ctx)
stop_context(context_id=analysis_ctx)
```

---

### 示例 5：Context 生命周期管理

```python
# 列出所有活跃 Context
contexts = list_contexts()
print(f"活跃 Context 数量: {contexts['total']}")

# 查找特定 Context
for ctx in contexts["contexts"]:
    print(f"- {ctx['name']}: {ctx['context_id']}")
    print(f"  创建时间: {ctx['created_at']}")
    print(f"  最后使用: {ctx['last_used']}")

# 清理超过 1 小时未使用的 Context
from datetime import datetime, timedelta

now = datetime.now()
for ctx in contexts["contexts"]:
    last_used = datetime.fromisoformat(ctx["last_used"].replace("Z", "+00:00"))
    if (now - last_used) > timedelta(hours=1):
        print(f"清理不活跃 Context: {ctx['name']}")
        stop_context(context_id=ctx["context_id"])
```

---

## 常见错误和解决方案

### 错误 1：未创建 Context 就执行代码

```python
# ❌ 错误：直接执行代码
run_code(code="x = 100", context_id="ctx-nonexistent")
# 错误: Context not found: ctx-nonexistent

# ✅ 正确：先创建 Context
ctx = create_context(name="my-task")["context_id"]
run_code(code="x = 100", context_id=ctx)
```

---

### 错误 2：使用已停止的 Context

```python
# 创建并停止 Context
ctx = create_context(name="temp")["context_id"]
stop_context(context_id=ctx)

# ❌ 错误：尝试在已停止的 Context 中执行
run_code(code="x = 100", context_id=ctx)
# 错误: Context not found: ctx-...

# ✅ 正确：重新创建新 Context
new_ctx = create_context(name="temp-new")["context_id"]
run_code(code="x = 100", context_id=new_ctx)
```

---

### 错误 3：忘记清理 Context

```python
# ❌ 不好的做法：创建大量 Context 不清理
for i in range(100):
    ctx = create_context(name=f"task-{i}")["context_id"]
    run_code(code="x = 100", context_id=ctx)
    # 忘记清理！

# ✅ 好的做法：使用完立即清理
for i in range(100):
    ctx = create_context(name=f"task-{i}")["context_id"]
    try:
        run_code(code="x = 100", context_id=ctx)
    finally:
        stop_context(context_id=ctx)  # 确保清理
```

---

## 最佳实践

### 1. Context 命名规范

推荐的命名模式：

```python
# 用户会话
create_context(name="user-{user_id}")
create_context(name="user-alice-session")

# 任务隔离
create_context(name="task-{task_name}")
create_context(name="task-data-cleaning")

# 临时测试
create_context(name="temp-{timestamp}")
create_context(name="temp-20251022-090000")

# 功能模块
create_context(name="module-{module_name}")
create_context(name="module-visualization")
```

---

### 2. 使用 Try-Finally 确保清理

```python
ctx = create_context(name="my-task")["context_id"]
try:
    # 执行代码
    run_code(code="x = 100", context_id=ctx)
    run_code(code="print(x)", context_id=ctx)
finally:
    # 确保清理
    stop_context(context_id=ctx)
```

---

### 3. 定期监控和清理

```python
import time

def cleanup_inactive_contexts(max_idle_seconds=3600):
    """清理超过指定时间未使用的 Context"""
    contexts = list_contexts()
    now = time.time()
    
    for ctx in contexts["contexts"]:
        last_used = datetime.fromisoformat(
            ctx["last_used"].replace("Z", "+00:00")
        ).timestamp()
        
        if (now - last_used) > max_idle_seconds:
            print(f"清理: {ctx['name']} (idle: {int(now - last_used)}s)")
            stop_context(context_id=ctx["context_id"])

# 定期调用
cleanup_inactive_contexts(max_idle_seconds=3600)  # 1小时
```

---

### 4. Context 生命周期模式

```python
class ContextManager:
    """Context 生命周期管理器"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.context_id = None
    
    def __enter__(self):
        # 创建 Context
        response = create_context(
            name=self.name,
            description=self.description
        )
        self.context_id = response["context_id"]
        return self.context_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理 Context
        if self.context_id:
            stop_context(context_id=self.context_id)
        return False

# 使用示例
with ContextManager(name="my-task") as ctx:
    run_code(code="x = 100", context_id=ctx)
    run_code(code="print(x)", context_id=ctx)
# 自动清理
```

---

## API 参考摘要

### create_context

```json
{
  "name": "create_context",
  "arguments": {
    "name": "string (必填)",
    "language": "python | javascript (可选，默认 python)",
    "description": "string (可选)"
  }
}
```

**返回**:
```json
{
  "context_id": "ctx-uuid",
  "name": "...",
  "language": "python" | "javascript",
  "status": "active",
  "created_at": "2025-10-22T09:00:00Z"
}
```

---

### run_code

```json
{
  "name": "run_code",
  "arguments": {
    "code": "string (必填)",
    "context_id": "string (必填)"
  }
}
```

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

### stop_context

```json
{
  "name": "stop_context",
  "arguments": {
    "context_id": "string (必填)"
  }
}
```

**返回**:
```json
{
  "context_id": "ctx-uuid",
  "status": "stopped",
  "message": "Context stopped successfully"
}
```

---

### list_contexts

```json
{
  "name": "list_contexts",
  "arguments": {}
}
```

**返回**:
```json
{
  "contexts": [
    {
      "context_id": "ctx-uuid",
      "name": "...",
      "status": "active",
      "created_at": "...",
      "last_used": "..."
    }
  ],
  "total": 1
}
```

---

## 总结

### 核心要点

1. ✅ **Context 必须显式创建** - 不能省略 create_context
2. ✅ **context_id 必须显式传递** - run_code 的必填参数
3. ✅ **完成后主动清理** - 使用 stop_context 释放资源
4. ✅ **定期监控** - 使用 list_contexts 检查活跃 Context

### 工作流程

```
创建 → 使用 → 清理
  ↓      ↓      ↓
create run_code stop
```

### 关键规则

- 🔴 **context_id 不可省略** - 每次 run_code 都必须指定
- 🔴 **停止后不可恢复** - stop_context 后需要重新创建
- 🟢 **状态持久化** - 同一 context_id 中变量保持
- 🟢 **跨 Session 共享** - Context 在所有 Session 间一致

---

**文档版本**: v2.2.0  
**最后更新**: 2025-10-22  
**支持语言**: Python, JavaScript  
**相关文档**: [TOOLS_API.md](./TOOLS_API.md), [SESSION_POOL_ARCHITECTURE.md](./SESSION_POOL_ARCHITECTURE.md)
