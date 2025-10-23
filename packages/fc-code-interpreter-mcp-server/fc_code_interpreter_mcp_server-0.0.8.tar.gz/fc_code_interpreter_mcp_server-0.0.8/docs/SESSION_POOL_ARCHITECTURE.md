# Session 池化架构设计

## 概述

本文档描述 AgentRun MCP 服务器的 Session 池化管理架构。该架构实现了：

- **单例 Code Interpreter**：一个长期运行的解释器实例
- **Session 池化管理**：3 个 Session 池化复用，60 分钟有效期
- **用户只管理 context_id**：Session 对用户透明，自动分配和管理
- **自动故障恢复**：Session 过期或失效时自动重建

---

## 核心概念

### 1. Code Interpreter（解释器）

- **单例模式**：整个服务器生命周期内只有一个解释器实例
- **启动时创建**：服务器启动时创建，约需 60 秒
- **长期运行**：直到服务器关闭才删除

### 2. Session（会话）

- **池化管理**：启动时创建 3 个 Session，池化复用
- **有效期**：每个 Session 有效期 60 分钟（固定，无法续期）
- **过期重建**：Session 过期后自动重建新 Session
- **用户透明**：用户无需管理 Session，由系统自动分配

### 3. Context（上下文）

- **用户管理**：用户通过 context_id 标识不同的执行环境
- **跨 Session 共享**：同一 context_id 在所有 Session 间保持状态一致
- **隔离机制**：不同 context_id 完全隔离，互不影响
- **持久化**：在服务器生命周期内持续存在

---

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentRun MCP Server                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Code Interpreter (单例)                      │    │
│  │         创建于启动时，直到关闭                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
│                           ├─── Session 池 (3 个) ────        │
│                           │                                   │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│    [Session-1]      [Session-2]      [Session-3]            │
│    60 分钟有效       60 分钟有效       60 分钟有效            │
│         │                 │                 │               │
│         └─────────────────┴─────────────────┘               │
│                           │                                   │
│              自动分配给 run_code 请求                          │
│                           │                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │     Context 管理 (用户创建和使用)                     │    │
│  │                                                       │    │
│  │  context_id: "default"     → 变量空间 1              │    │
│  │  context_id: "user-alice"  → 变量空间 2              │    │
│  │  context_id: "user-bob"    → 变量空间 3              │    │
│  │  context_id: "task-123"    → 变量空间 4              │    │
│  │                                                       │    │
│  │  每个 Context 在所有 Session 间共享状态               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Session 池化流程

### 启动流程

```
1. MCP Server 启动
   ↓
2. 创建 Code Interpreter 实例
   - 等待约 60 秒
   - 状态轮询直到 READY
   ↓
3. 初始化 Session 池
   - 创建 Session-1 (60 分钟有效期)
   - 创建 Session-2 (60 分钟有效期)
   - 创建 Session-3 (60 分钟有效期)
   ↓
4. 自动健康检查
   - 验证 Interpreter 状态
   - 验证所有 Session 可用
   - 记录健康状态日志
   ↓
5. 服务器就绪
   - 开始接受请求
   - 后台监控 Session 过期
```

### 代码执行流程

```
用户请求: run_code(code="x = 100", context_id="user-alice")
   ↓
1. 从 Session 池获取可用 Session
   - 检查是否有空闲 Session
   - 如果 Session 过期，先重建
   - 标记为 active（正在使用）
   ↓
2. 执行代码
   - 使用获取的 Session
   - 指定 context_id="user-alice"
   - 代码在 user-alice 的上下文中执行
   ↓
3. 返回结果
   - stdout, stderr, success, execution_time
   ↓
4. 释放 Session 回池
   - 标记为 available（可用）
   - 可以被下次请求使用
```

### Session 过期处理

```
后台监控线程（每 5 分钟检查一次）
   ↓
检查每个 Session 的创建时间
   ↓
如果 Session 已使用超过 60 分钟
   ↓
1. 删除旧 Session（如果可能）
2. 创建新 Session（60 分钟有效期）
3. 替换池中的旧 Session
   ↓
池中始终保持 3 个可用 Session
```

---

## 端到端使用场景

### 场景 1：单用户执行代码

```python
# 用户 Alice 执行代码（使用默认 context）

# 请求 1
run_code(code="x = 100")
# → 自动分配 Session-1
# → 在 "default" context 中执行
# → 结果: x = 100 已设置
# → 释放 Session-1

# 请求 2（继续使用相同 context）
run_code(code="print(x)")
# → 自动分配 Session-2（或 Session-1 如果可用）
# → 在 "default" context 中执行
# → 结果: stdout="100\n"（变量 x 仍然存在）
# → 释放 Session
```

**关键点**：
- 用户无需指定 session_id
- 默认使用 "default" context
- 变量在同一 context 中持久化

---

### 场景 2：多用户隔离执行

```python
# 用户 Alice
create_context(name="user-alice")
# → 返回 context_id: "ctx-a1b2c3..."

run_code(code="x = 'Alice'", context_id="ctx-a1b2c3...")
# → 自动分配 Session-1
# → 在 Alice 的 context 中执行
# → 释放 Session-1

# 用户 Bob
create_context(name="user-bob")
# → 返回 context_id: "ctx-d4e5f6..."

run_code(code="x = 'Bob'", context_id="ctx-d4e5f6...")
# → 自动分配 Session-2
# → 在 Bob 的 context 中执行
# → 释放 Session-2

# Alice 继续执行
run_code(code="print(x)", context_id="ctx-a1b2c3...")
# → 自动分配 Session-3
# → 在 Alice 的 context 中执行
# → 结果: stdout="Alice\n"（Bob 的 x 不影响 Alice）
# → 释放 Session-3

# Bob 继续执行
run_code(code="print(x)", context_id="ctx-d4e5f6...")
# → 自动分配 Session-1（已释放，可复用）
# → 在 Bob 的 context 中执行
# → 结果: stdout="Bob\n"（Alice 的 x 不影响 Bob）
# → 释放 Session-1
```

**关键点**：
- 每个用户有独立的 context_id
- Session 在用户间复用，但 context 隔离保证状态不混淆
- 用户无需关心 Session 分配

---

### 场景 3：并发执行（最多 3 个）

```python
# 3 个并发请求（同时到达）

# 请求 A
run_code(code="import time; time.sleep(5); print('A')", context_id="task-1")
# → 获取 Session-1
# → 执行中...

# 请求 B（并发）
run_code(code="import time; time.sleep(5); print('B')", context_id="task-2")
# → 获取 Session-2
# → 执行中...

# 请求 C（并发）
run_code(code="import time; time.sleep(5); print('C')", context_id="task-3")
# → 获取 Session-3
# → 执行中...

# 请求 D（并发）- 所有 Session 都在使用中
run_code(code="print('D')", context_id="task-4")
# → 等待可用 Session...
# → 当请求 A/B/C 中任意一个完成时
# → 获取释放的 Session
# → 执行并返回
```

**关键点**：
- 最多同时执行 3 个请求（Session 池大小）
- 第 4 个请求会阻塞等待
- 自动排队机制，无需用户处理

---

### 场景 4：Session 过期自动重建

```python
# 服务器启动（假设时间 T0）
# Session-1 创建于 T0
# Session-2 创建于 T0
# Session-3 创建于 T0

# ... 55 分钟后（T0 + 55min）...
run_code(code="x = 100", context_id="ctx-123")
# → 获取 Session-1（还有 5 分钟到期）
# → 执行成功
# → 释放 Session-1

# ... 6 分钟后（T0 + 61min）...
# 后台监控检测到 Session-1/2/3 已过期（>60 分钟）

# 自动重建流程（对用户透明）:
# 1. 删除 Session-1，创建新 Session-1（有效期到 T0 + 121min）
# 2. 删除 Session-2，创建新 Session-2（有效期到 T0 + 121min）
# 3. 删除 Session-3，创建新 Session-3（有效期到 T0 + 121min）

# 用户请求继续正常
run_code(code="print(x)", context_id="ctx-123")
# → 获取新的 Session-1
# → Context "ctx-123" 中的 x 仍然存在
# → 执行成功
# → 释放 Session-1
```

**关键点**：
- Session 过期自动重建，用户无感知
- Context 数据独立于 Session，不会丢失
- 重建过程对执行请求透明

---

## Context 与 Session 的关系

### Context 是什么？

Context 是**变量空间**的逻辑标识符：
- 每个 context_id 代表一个独立的变量空间
- 变量、导入、函数定义等都存储在 Context 中
- Context 在所有 Session 间共享

### Session 是什么？

Session 是**执行容器**：
- Session 是实际执行代码的环境
- Session 从池中分配，执行完成后释放
- Session 只是临时的执行载体，不存储状态

### 关系示意

```
Context (逻辑层)              Session (物理层)
───────────────              ───────────────
"default"                    Session-1
  └─ x = 100                   ├─ 执行 code
  └─ y = 200      ──读取──>    └─ 使用 context="default"
                   <──写入──

"user-alice"                 Session-2
  └─ name = "Alice"            ├─ 执行 code
  └─ age = 25     ──读取──>    └─ 使用 context="user-alice"
                   <──写入──

"user-bob"                   Session-3
  └─ name = "Bob"              ├─ 执行 code
  └─ age = 30     ──读取──>    └─ 使用 context="user-bob"
                   <──写入──
```

**类比**：
- **Context** 就像数据库中的"表"（存储数据）
- **Session** 就像"数据库连接"（执行查询，用完释放）

---

## 优势与权衡

### 优势

1. **用户体验简单**
   - 用户只需管理 context_id
   - 无需关心 Session 生命周期
   - 自动故障恢复

2. **资源高效**
   - 单个 Code Interpreter 实例
   - 3 个 Session 池化复用
   - 避免频繁创建/删除

3. **并发支持**
   - 最多同时 3 个请求并发执行
   - 自动排队和分配

4. **自动管理**
   - Session 过期自动重建
   - Context 数据自动同步
   - 故障自动恢复

### 权衡

1. **并发限制**
   - 最多同时 3 个请求
   - 第 4 个请求需要等待
   - **缓解方案**：增加 Session 池大小（可配置）

2. **Session 无法续期**
   - Session 过期必须重建
   - 重建有短暂延迟
   - **缓解方案**：后台主动监控，提前重建

3. **Context 跨 Session 同步**
   - 需要底层 AgentRun 支持 Context 机制
   - 如果不支持，需要在数据面实现
   - **缓解方案**：使用共享存储或缓存

---

## 实施要点

### 1. Session 池管理

```python
class SessionPool:
    def __init__(self, size=3):
        self.size = size
        self.sessions: List[SessionInfo] = []
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> SessionInfo:
        """获取可用 Session，如果都在用则等待"""
        while True:
            async with self.lock:
                for session in self.sessions:
                    if not session.is_active:
                        if self._is_expired(session):
                            await self._rebuild_session(session)
                        session.is_active = True
                        return session
            # 所有 Session 都在使用，等待 100ms 后重试
            await asyncio.sleep(0.1)
    
    async def release(self, session_id: str):
        """释放 Session 回池"""
        async with self.lock:
            for session in self.sessions:
                if session.session_id == session_id:
                    session.is_active = False
                    break
```

### 2. Context 隔离

```python
# 在 run_code 请求中传递 context_id
async def execute_code(session_id: str, code: str, context_id: str):
    # 数据面 API 调用示例
    response = await data_plane_client.post(
        f"/v1/sessions/{session_id}/execute",
        json={
            "code": code,
            "context_id": context_id,  # 关键：指定 context
            "timeout": 30
        }
    )
    return response
```

### 3. 过期监控

```python
async def session_monitor_loop():
    """后台任务：定期检查 Session 过期"""
    while True:
        await asyncio.sleep(300)  # 每 5 分钟检查一次
        
        async with session_pool.lock:
            for i, session in enumerate(session_pool.sessions):
                if session_pool._is_expired(session) and not session.is_active:
                    # 重建过期的 Session
                    new_session = await create_new_session()
                    session_pool.sessions[i] = new_session
                    logger.info(f"Session {session.session_id} 过期，已重建")
```

---

## 自动健康检查

服务器在 Session 池初始化后会**自动执行内部健康检查**，这不是 MCP 工具，而是内部功能。

### 检查内容

```python
async def perform_health_check():
    # 1. 验证 Interpreter 状态 = READY
    assert agentrun_manager.is_ready
    
    # 2. 验证 Session 池大小 = 3
    assert len(agentrun_manager.session_pool) == 3
    
    # 3. 验证所有 Session 有效
    for session in agentrun_manager.session_pool:
        assert session.session_id is not None
    
    # 4. 记录启动日志
    logger.info("✓ 健康检查通过")
```

### 日志示例

```
[INFO] AgentRun 初始化开始...
[INFO] 创建 Code Interpreter: ci-abc123
[INFO] Interpreter 状态: READY
[INFO] 初始化 Session 池 (大小: 3)...
[INFO] Session-1 创建成功
[INFO] Session-2 创建成功
[INFO] Session-3 创建成功
[INFO] 执行健康检查...
[INFO] ✓ Interpreter 就绪
[INFO] ✓ Session 池健康 (3/3 可用)
[INFO] ✓ 所有 Session 验证通过
[INFO] 服务器启动完成，耗时: 65 秒
[INFO] MCP Server 就绪，等待请求...
```

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `SESSION_POOL_SIZE` | 3 | Session 池大小 |
| `SESSION_LIFETIME` | 3600 秒 | Session 有效期（60 分钟） |
| `SESSION_CHECK_INTERVAL` | 300 秒 | 过期检查间隔（5 分钟） |
| `DEFAULT_CONTEXT_ID` | "default" | 默认 Context ID |
| `EXECUTION_TIMEOUT` | 30 秒 | 代码执行超时 |
| `AUTO_HEALTH_CHECK` | true | 启动时自动健康检查（始终开启） |

---

## 总结

Session 池化架构的核心思想：

1. **用户只管理 Context**（变量空间）
2. **系统自动管理 Session**（执行容器）
3. **Context 跨 Session 共享**（状态持久化）
4. **Session 池化复用**（资源高效）
5. **自动故障恢复**（过期重建）

这种架构为用户提供了简单、透明的使用体验，同时最大化了资源利用效率。

---

**文档版本**: v2.0.0  
**最后更新**: 2025-10-22  
**架构状态**: 设计完成，待实施
