# AgentRun MCP 服务器实施计划
## 单例解释器 + Session 池化管理架构

## 概述

本实施采用：
- **1 个 Code Interpreter 实例**：在服务器启动时创建，单例模式，所有请求重用
- **Session 池化管理**：启动时初始化 3 个 Session，自动管理生命周期（60 分钟）
- **用户只管理 context_id**：无需关心 Session，通过 context_id 隔离不同任务
- **自动故障恢复**：Session 过期或失效时自动重建

## 架构图

```
MCP 服务器启动
    ↓
创建单个 Code Interpreter 实例（等待 60 秒）
    ↓
初始化 Session 池（3 个 Session，每个 60 分钟有效期）
    ↓
服务器就绪可接受请求
    ↓
┌─────────────────────────────────────────────────────────────┐
│                     Session 池 (3 个)                         │
│   [Session-1] [Session-2] [Session-3]                     │
│        │            │            │                        │
│        └────────────┼────────────┘                        │
│                     │                                       │
│              自动分配给请求                              │
│                     │                                       │
│  请求 1: run_code(code, context_id="user-alice")            │
│     → 获取 Session-1 → 执行 → 释放 Session-1           │
│                                                               │
│  请求 2: run_code(code, context_id="user-bob")              │
│     → 获取 Session-2 → 执行 → 释放 Session-2           │
│                                                               │
│  请求 3: run_code(code, context_id="user-alice")            │
│     → 获取 Session-1 → 执行（复用 context）→ 释放       │
│                                                               │
│  Context 在所有 Session 间共享，Session 只是执行容器      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
    ↓
后台线程：监控 Session 过期（60 分钟）→ 自动重建
    ↓
服务器关闭
    ↓
删除所有 Session + 删除 Interpreter + 清理
```

## 优势

1. **快速响应**：无需每次请求创建 Session，从池中快速获取
2. **资源高效**：单个 Code Interpreter 实例 + 3 个 Session 池化复用
3. **用户友好**：用户只需管理 context_id，无需关心 Session 生命周期
4. **自动管理**：Session 过期自动重建，对用户透明
5. **Context 隔离**：不同 context_id 完全隔离，防止任务间冲突
6. **并发支持**：最多同时 3 个请求并发执行

## 实施步骤

### 步骤 1：项目结构

```
packages/python/
├── mcp_server/
│   ├── __init__.py           # 入口点
│   ├── server.py             # 主 MCP 服务器逻辑
│   ├── agentrun_manager.py   # 新增：AgentRun 生命周期管理器
│   └── data_plane_client.py  # 新增：数据面客户端
├── pyproject.toml            # 更新依赖项
└── .env.example              # 新增：环境变量模板
```

### 步骤 2：更新依赖项

**文件：`packages/python/pyproject.toml`**

```toml
[tool.poetry.dependencies]
python = ">=3.10,<4.0"

# 移除 E2B
# e2b-code-interpreter = "^1.0.2"

# 添加 AgentRun 依赖
mcp = "^1.0.0"
pydantic = "^2.10.2"
python-dotenv = "1.0.1"
alibabacloud-agentrun20250910 = "^1.0.0"
alibabacloud-credentials = "^0.3.0"
alibabacloud-tea-openapi = "^0.3.0"
httpx = "^0.27.0"
```

### 步骤 3：创建 AgentRun 管理器

**文件：`packages/python/mcp_server/agentrun_manager.py`**

完整代码见英文版 `IMPLEMENTATION_PLAN.md` 第 3 步（约 330 行）

**关键功能**：

```python
class AgentRunManager:
    """管理单例 Code Interpreter + Session 池"""
    
    def __init__(self, config: InterpreterConfig, pool_size: int = 3):
        self.config = config
        self.pool_size = pool_size  # Session 池大小，默认 3
        self.session_pool: List[SessionInfo] = []  # Session 池
        self.session_lock = asyncio.Lock()  # 池锁
        self.active_sessions: Set[str] = set()  # 正在使用的 Session
    
    async def initialize(self):
        """初始化控制面客户端、创建解释器、初始化 Session 池"""
        # 1. 创建凭证和控制面客户端
        # 2. 创建 Code Interpreter 实例
        # 3. 等待就绪状态（轮询）
        # 4. 初始化 Session 池（3 个 Session）
    
    async def _init_session_pool(self):
        """初始化 Session 池，创建 pool_size 个 Session"""
        for i in range(self.pool_size):
            session = await self._create_new_session()
            self.session_pool.append(session)
    
    async def _create_new_session(self) -> SessionInfo:
        """创建一个新 Session（60 分钟有效期）"""
        # 通过控制面 API 创建 Session
        # 记录创建时间，用于过期检测
        # 返回 SessionInfo 对象
    
    async def acquire_session(self) -> SessionInfo:
        """从池中获取一个可用 Session（阻塞式）"""
        async with self.session_lock:
            # 1. 找到第一个未被使用的 Session
            # 2. 检查是否过期，如过期则重建
            # 3. 标记为 active
            # 4. 返回 Session
    
    async def release_session(self, session_id: str):
        """释放 Session 回池"""
        async with self.session_lock:
            self.active_sessions.discard(session_id)
    
    async def _is_session_expired(self, session: SessionInfo) -> bool:
        """检查 Session 是否过期（60 分钟）"""
        elapsed = time.time() - session.created_at
        return elapsed >= 3600  # 60 分钟 = 3600 秒
    
    async def cleanup(self):
        """清理所有 Session 和 Code Interpreter"""
        # 删除所有 Session
        # 删除 Interpreter 实例
        # 清空池
```

**关键数据类**：

```python
@dataclass
class InterpreterConfig:
    """解释器配置"""
    access_key_id: str
    access_key_secret: str
    account_id: str
    region: str = "cn-hangzhou"
    name: str = "mcp-server-interpreter"
    cpu: float = 2.0
    memory: int = 2048
    session_timeout: int = 3600

@dataclass
class SessionInfo:
    """会话信息"""
    session_id: str
    code_interpreter_id: str
    tenant_id: str
    data_endpoint: str
    created_at: float  # 创建时间戳，用于计算是否过期
    expires_at: float  # 过期时间戳 (created_at + 3600)
    is_active: bool = False  # 是否正在使用
```

### 步骤 4：创建数据面客户端

**文件：`packages/python/mcp_server/data_plane_client.py`**

完整代码见英文版 `IMPLEMENTATION_PLAN.md` 第 4 步（约 130 行）

**关键功能**：

```python
class DataPlaneClient:
    """AgentRun 数据面客户端 - 通过 HTTP API 执行代码"""
    
    async def execute_code(
        self,
        code_interpreter_id: str,
        session_id: str,
        code: str,
        context_id: str = "default",
        execution_timeout: int = 30,
    ) -> ExecutionResult:
        """在解释器中执行 Python 代码"""
        # 构建 HTTP 请求
        # POST 到数据面 API
        # 返回执行结果

@dataclass
class ExecutionResult:
    """代码执行结果"""
    stdout: str
    stderr: str
    success: bool
    execution_time: Optional[float] = None
```

### 步骤 5：更新 MCP 服务器

**文件：`packages/python/mcp_server/server.py`**

完整代码见英文版 `IMPLEMENTATION_PLAN.md` 第 5 步（约 180 行）

**关键变更**：

```python
# 全局状态
agentrun_manager: Optional[AgentRunManager] = None
data_client: Optional[DataPlaneClient] = None
context_registry: Dict[str, ContextInfo] = {}  # Context 注册表

async def initialize_agentrun():
    """服务器启动时初始化 AgentRun 管理器"""
    global agentrun_manager, data_client
    
    # 1. 加载配置
    config = InterpreterConfig(...)
    
    # 2. 创建并初始化管理器（包含 Session 池）
    agentrun_manager = AgentRunManager(config, pool_size=3)
    await agentrun_manager.initialize()  # 约 60 秒 + 创建 3 个 Session
    
    # 3. 创建数据面客户端
    data_client = DataPlaneClient(...)
    
    # 4. 自动执行健康检查
    await perform_health_check()
    
    logger.info("AgentRun 初始化完成，Session 池大小: %d", agentrun_manager.pool_size)

async def perform_health_check():
    """自动执行内部健康检查"""
    logger.info("执行健康检查...")
    
    try:
        # 检查 Interpreter 状态
        if not agentrun_manager.is_ready:
            raise RuntimeError("Interpreter 未就绪")
        logger.info("✓ Interpreter 就绪")
        
        # 检查 Session 池
        pool_size = len(agentrun_manager.session_pool)
        if pool_size != agentrun_manager.pool_size:
            raise RuntimeError(f"Session 池大小不匹配: {pool_size}/{agentrun_manager.pool_size}")
        logger.info(f"✓ Session 池健康 ({pool_size}/{agentrun_manager.pool_size} 可用)")
        
        # 验证所有 Session
        for i, session in enumerate(agentrun_manager.session_pool):
            if not session.session_id:
                raise RuntimeError(f"Session-{i+1} 无效")
        logger.info("✓ 所有 Session 验证通过")
        
        # 计算启动时间
        startup_time = int(time.time() - agentrun_manager.start_time)
        logger.info(f"服务器启动完成，耗时: {startup_time} 秒")
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise

async def cleanup_agentrun():
    """服务器关闭时清理 AgentRun 资源"""
    if data_client:
        await data_client.close()
    if agentrun_manager:
        await agentrun_manager.cleanup()

@app.list_tools()
async def list_tools():
    """列出可用工具"""
    return [
        Tool(
            name="run_code",
            description="在 AgentRun 的安全沙箱中运行 Python 代码。Session 自动从池分配，使用 context_id 进行隔离。",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "context_id": {"type": "string", "description": "执行上下文 ID，默认 'default'"}
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="create_context",
            description="创建一个新的隔离代码执行上下文",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "上下文名称"},
                    "description": {"type": "string", "description": "上下文描述"}
                },
                "required": ["name"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    """处理工具调用"""
    
    if name == "run_code":
        # 验证参数
        arguments = RunCodeSchema.model_validate(arguments)
        context_id = arguments.context_id or "default"
        
        # 从 Session 池获取可用 Session
        session = await agentrun_manager.acquire_session()
        
        try:
            # 执行代码
            result = await data_client.execute_code(
                code_interpreter_id=agentrun_manager.interpreter_id,
                session_id=session.session_id,
                code=arguments.code,
                context_id=context_id,  # 用户指定的 context
                execution_timeout=30,
            )
            
            # 返回结果
            return [TextContent(
                type="text", 
                text=json.dumps({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.success,
                    "execution_time": result.execution_time
                }, indent=2)
            )]
        finally:
            # 释放 Session 回池
            await agentrun_manager.release_session(session.session_id)
    
    elif name == "create_context":
        # 创建 Context
        arguments = CreateContextSchema.model_validate(arguments)
        context_id = f"ctx-{uuid.uuid4()}"
        
        context_registry[context_id] = ContextInfo(
            context_id=context_id,
            name=arguments.name,
            description=arguments.description or "",
            created_at=time.time()
        )
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "context_id": context_id,
                "name": arguments.name,
                "description": arguments.description or "",
                "language": "python",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "status": "active",
                "message": "上下文创建成功"
            }, indent=2)
        )]

async def main():
    """主入口点"""
    await initialize_agentrun()  # 启动前初始化
    try:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(...)
    finally:
        await cleanup_agentrun()  # 关闭时清理
```

### 步骤 6：更新入口点

**文件：`packages/python/mcp_server/__init__.py`**

```python
from . import server
import asyncio

def main():
    """包的主入口点"""
    asyncio.run(server.main())

__all__ = ['main', 'server']
```

### 步骤 7：环境变量配置

**文件：`packages/python/.env.example`**

```bash
# AgentRun 认证
AGENTRUN_ACCESS_KEY_ID=your_access_key_id
AGENTRUN_ACCESS_KEY_SECRET=your_access_key_secret
AGENTRUN_ACCOUNT_ID=your_account_id

# AgentRun 配置
AGENTRUN_REGION=cn-hangzhou
AGENTRUN_INTERPRETER_NAME=mcp-server-interpreter

# 资源配置
AGENTRUN_CPU=2.0
AGENTRUN_MEMORY=2048
AGENTRUN_SESSION_TIMEOUT=3600
```

## 测试

### 1. 本地测试

```bash
# 设置环境变量
export AGENTRUN_ACCESS_KEY_ID="your_key"
export AGENTRUN_ACCESS_KEY_SECRET="your_secret"
export AGENTRUN_ACCOUNT_ID="your_account"

# 使用 MCP Inspector 运行
cd packages/python
npx @modelcontextprotocol/inspector \
  uv \
  --directory . \
  run \
  e2b-mcp-server
```

### 2. 测试用例

1. **服务器启动**（约 1 分钟）
   - 验证解释器创建
   - 检查会话初始化
   - 确认就绪状态

2. **代码执行**
   ```python
   # 测试 1：简单打印
   print("Hello from AgentRun!")
   
   # 测试 2：状态持久化
   x = 42  # 先运行这个
   print(x)  # 再运行这个 - 应该打印 42
   
   # 测试 3：错误处理
   undefined_variable  # 应该返回 stderr
   ```

3. **服务器关闭**
   - 验证清理日志
   - 确认解释器删除

## 增强功能（未来）

1. **每客户端会话**
   ```python
   # 从 MCP 上下文提取客户端 ID
   client_id = get_client_id_from_context()
   session_id = f"client-{client_id}"
   
   # 获取或创建会话
   session = await agentrun_manager.create_session(session_id)
   ```

2. **会话池**
   - 启动时预创建 N 个会话
   - 轮换会话以实现负载均衡

3. **健康监控**
   - 定期健康检查
   - 故障自动恢复
   - 指标收集

4. **优雅降级**
   - 如果 AgentRun 不可用，回退到 E2B
   - 初始化期间排队请求

## 时间线

- **第 1 天**：实施核心组件（agentrun_manager、data_plane_client）
- **第 2 天**：更新 MCP 服务器集成
- **第 3 天**：测试和调试
- **第 4 天**：文档和部署

## 成功标准

- ✅ 服务器在 2 分钟内启动（包括解释器创建）
- ✅ 代码执行正常工作
- ✅ 状态在会话内持久化
- ✅ 优雅关闭清理资源
- ✅ 错误处理正常工作

## 完整代码

详细的完整代码实现，请参阅英文版 `IMPLEMENTATION_PLAN.md` 文档。中文版提供架构和关键部分概述，完整的可运行代码在英文文档中提供。

## 关键要点

1. **启动延迟**：服务器首次启动需要约 60 秒来创建解释器
2. **单例模式**：一个解释器实例服务所有请求
3. **会话隔离**：每个客户端可以有自己的会话
4. **优雅清理**：使用 `finally` 块确保资源被清理
5. **错误处理**：适当的异常处理和日志记录
6. **轮询机制**：等待解释器就绪使用轮询而非阻塞

## 注意事项

⚠️ **重要**：首次运行时请耐心等待，解释器创建需要时间  
⚠️ **重要**：确保所有环境变量都已正确设置  
⚠️ **重要**：测试时监控日志输出以诊断问题  
⚠️ **重要**：在生产环境部署前进行充分测试
