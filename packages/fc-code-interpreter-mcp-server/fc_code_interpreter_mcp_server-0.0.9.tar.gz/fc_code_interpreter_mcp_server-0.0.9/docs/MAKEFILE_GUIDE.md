# Makefile 使用指南

## 快速开始

### 1. 安装依赖
```bash
make install
```

### 2. 启动 MCP Server
```bash
make run
# 或者
make server
# 或者
make start
```

MCP Server 将以 stdio 模式启动，适合与 Claude Desktop 等客户端集成。

### 3. 使用 MCP Inspector 调试
```bash
make inspector
# 或者
make debug
```

这将启动 MCP Inspector Web 界面，方便测试和调试 MCP 工具。

## 环境变量配置

默认配置：
- `ENVD_URL=http://localhost:5001` - Code Interpreter 端点

### 自定义配置

```bash
# 使用自定义 Code Interpreter 端点
ENVD_URL=http://your-endpoint:5001 make run

# 或者修改 .env 文件
echo "ENVD_URL=http://your-endpoint:5001" > .env
make run
```

## 测试命令

### 运行所有测试
```bash
make test
```

### 运行特定测试

```bash
# E2B 集成测试
make test-integration

# Sandbox 功能测试
make test-sandbox

# MCP Server 集成测试
make test-mcp
```

## 开发命令

### 开发环境设置
```bash
make dev
```

这将安装依赖并显示可用命令。

### 清理临时文件
```bash
make clean
```

## 发布命令

### 构建 Python 包
```bash
make build
```

### 发布到 PyPI
```bash
make publish
```

## 常用工作流

### 本地开发测试
```bash
# 1. 确保 Code Interpreter 服务运行在 localhost:5001
# 2. 安装依赖
make install

# 3. 运行测试
make test

# 4. 启动 Inspector 调试
make inspector
```

### 与 Claude Desktop 集成
```bash
# 1. 配置 claude_desktop_config.json
# 2. 启动 MCP Server
make run
```

配置示例：
```json
{
  "mcpServers": {
    "agentrun": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/sandbox-code-interpreter-mcp-server",
        "run",
        "agentrun-mcp-server"
      ],
      "env": {
        "ENVD_URL": "http://localhost:5001"
      }
    }
  }
}
```

## 命令别名

| 原命令 | 别名 | 说明 |
|--------|------|------|
| `make run` | `make server`, `make start` | 启动 MCP Server |
| `make inspector` | `make debug` | 启动 Inspector 调试 |

## 故障排除

### 问题：Code Interpreter 连接失败

**解决方案：**
1. 检查 Code Interpreter 服务是否运行
   ```bash
   curl http://localhost:5001/health
   ```

2. 检查 ENVD_URL 配置
   ```bash
   echo $ENVD_URL
   ```

3. 查看 .env 文件
   ```bash
   cat .env
   ```

### 问题：测试失败

**解决方案：**
1. 确保 Code Interpreter 服务正在运行
2. 重新安装依赖
   ```bash
   make clean
   make install
   ```

## 获取帮助

查看所有可用命令：
```bash
make help
```
