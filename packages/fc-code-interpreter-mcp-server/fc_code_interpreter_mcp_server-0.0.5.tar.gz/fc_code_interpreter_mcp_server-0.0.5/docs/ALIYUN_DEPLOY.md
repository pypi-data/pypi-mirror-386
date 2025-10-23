# 阿里云镜像部署指南

本指南介绍如何使用阿里云容器镜像仓库中的镜像快速部署 MCP Server 和 Sandbox。

## 🚀 快速开始

### 前提条件

- 安装 Docker 和 Docker Compose
- 确保可以访问阿里云容器镜像服务

### 一键部署

```bash
# 使用阿里云镜像部署
docker-compose -f docker-compose.aliyun.yml up -d
```

## 📦 镜像说明

### 使用的镜像

| 服务 | 镜像地址 | 说明 |
|------|---------|------|
| **Sandbox** | `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-v0.2.2` | 代码执行引擎 |
| **MCP Server** | `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest` | MCP 协议服务器 |

### 网络架构

```
┌─────────────────────────────────────────────┐
│         Docker Network: sandbox-net         │
├─────────────────────────────────────────────┤
│                                             │
│  ┌────────────────────────────────────┐    │
│  │   mcp-server                       │    │
│  │   Port: 3000 (external)            │    │
│  │   Image: ...-mcp-latest            │    │
│  └────────────┬───────────────────────┘    │
│               │                             │
│               │ http://sandbox-code-        │
│               │   interpreter:8080          │
│               ▼                             │
│  ┌────────────────────────────────────┐    │
│  │   sandbox-code-interpreter         │    │
│  │   Port: 5001 (external) -> 8080    │    │
│  │   Image: ...-v0.2.2                │    │
│  └────────────────────────────────────┘    │
│                                             │
└─────────────────────────────────────────────┘
```

## 🔧 配置说明

### 端口映射

| 服务 | 容器端口 | 主机端口 | 访问地址 |
|------|---------|---------|---------|
| Sandbox | 8080 | 5001 | http://localhost:5001 |
| MCP Server | 3000 | 3000 | http://localhost:3000/sse |

### 环境变量

#### Sandbox 配置

```yaml
SANDBOX_ENV: production           # 运行环境
SANDBOX_HOST: 0.0.0.0            # 监听地址
SANDBOX_PORT: 8080               # 容器内端口
SANDBOX_DEBUG: false             # 调试模式
SANDBOX_LOG_LEVEL: info          # 日志级别
SANDBOX_WORKSPACE_DIR: /workspace # 工作目录
SANDBOX_MAX_CONTEXTS: 100        # 最大上下文数
```

#### MCP Server 配置

```yaml
SANDBOX_URL: http://sandbox-code-interpreter:8080  # Sandbox 内部地址
MCP_HOST: 0.0.0.0                                  # 监听地址
MCP_PORT: 3000                                     # 端口
LOG_LEVEL: INFO                                    # 日志级别
```

## 📋 常用命令

### 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.aliyun.yml up -d

# 查看服务状态
docker-compose -f docker-compose.aliyun.yml ps

# 查看日志
docker-compose -f docker-compose.aliyun.yml logs -f
```

### 停止服务

```bash
# 停止所有服务
docker-compose -f docker-compose.aliyun.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.aliyun.yml down -v
```

### 服务管理

```bash
# 重启服务
docker-compose -f docker-compose.aliyun.yml restart

# 重启单个服务
docker-compose -f docker-compose.aliyun.yml restart mcp-server

# 查看 MCP Server 日志
docker-compose -f docker-compose.aliyun.yml logs -f mcp-server

# 查看 Sandbox 日志
docker-compose -f docker-compose.aliyun.yml logs -f sandbox-code-interpreter

# 进入容器
docker-compose -f docker-compose.aliyun.yml exec mcp-server /bin/bash
```

## 🔍 验证部署

### 1. 检查服务状态

```bash
docker-compose -f docker-compose.aliyun.yml ps
```

预期输出：
```
NAME                       IMAGE                                                                          STATUS
sandbox-code-interpreter   registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-inte...      Up (healthy)
sandbox-mcp-server         registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-inte...      Up (healthy)
```

### 2. 测试 Sandbox

```bash
curl http://localhost:5001/health
```

预期响应：
```json
{"status":"healthy"}
```

### 3. 测试 MCP Server

```bash
# 测试 SSE 端点 (会持续连接，Ctrl+C 退出)
timeout 2 curl -I http://localhost:3000/sse
```

预期响应：
```
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
...
```

### 4. 使用 MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:3000/sse
```

## 🔄 更新镜像

### 拉取最新镜像

```bash
# 拉取最新的 MCP Server 镜像
docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest

# 拉取特定版本的 Sandbox 镜像
docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-v0.2.2
```

### 重新部署

```bash
# 停止服务
docker-compose -f docker-compose.aliyun.yml down

# 拉取最新镜像
docker-compose -f docker-compose.aliyun.yml pull

# 启动服务
docker-compose -f docker-compose.aliyun.yml up -d
```

## 🐛 故障排查

### 问题 1: 无法拉取镜像

**错误信息**:
```
Error response from daemon: Get https://registry.cn-hangzhou.aliyuncs.com/v2/: unauthorized
```

**解决方案**:
```bash
# 登录阿里云容器镜像服务
docker login registry.cn-hangzhou.aliyuncs.com
```

### 问题 2: 端口冲突

**错误信息**:
```
Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use
```

**解决方案**:
```bash
# 检查端口占用
lsof -i :3000
lsof -i :5001

# 停止占用端口的进程或修改 docker-compose.aliyun.yml 中的端口映射
```

### 问题 3: Sandbox 健康检查失败

```bash
# 查看 Sandbox 日志
docker-compose -f docker-compose.aliyun.yml logs sandbox-code-interpreter

# 手动测试健康检查
docker-compose -f docker-compose.aliyun.yml exec sandbox-code-interpreter curl -f http://localhost:8080/health
```

### 问题 4: MCP Server 无法连接 Sandbox

```bash
# 检查网络连接
docker-compose -f docker-compose.aliyun.yml exec mcp-server curl http://sandbox-code-interpreter:8080/health

# 查看网络配置
docker network inspect sandbox-code-interpreter-mcp-server_sandbox-net
```

## 🔧 自定义配置

### 修改镜像版本

编辑 `docker-compose.aliyun.yml`:

```yaml
services:
  sandbox-code-interpreter:
    # 使用特定版本
    image: registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-v0.2.3
  
  mcp-server:
    # 使用特定 commit 版本
    image: registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-c4d85cb
```

### 添加环境变量

```yaml
services:
  mcp-server:
    environment:
      - SANDBOX_URL=http://sandbox-code-interpreter:8080
      - MCP_HOST=0.0.0.0
      - MCP_PORT=3000
      - LOG_LEVEL=DEBUG  # 修改日志级别
      # 添加自定义变量
      - CUSTOM_VAR=value
```

### 资源限制

```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## 📊 监控和日志

### 实时日志

```bash
# 所有服务日志
docker-compose -f docker-compose.aliyun.yml logs -f

# 只看 MCP Server
docker-compose -f docker-compose.aliyun.yml logs -f mcp-server

# 最近 100 行
docker-compose -f docker-compose.aliyun.yml logs --tail=100
```

### 导出日志

```bash
# 导出到文件
docker-compose -f docker-compose.aliyun.yml logs > logs.txt

# 按服务导出
docker-compose -f docker-compose.aliyun.yml logs mcp-server > mcp-server.log
docker-compose -f docker-compose.aliyun.yml logs sandbox-code-interpreter > sandbox.log
```

## 📚 相关文档

- [Docker Compose 文件](docker-compose.aliyun.yml)
- [镜像构建指南](IMAGE_BUILD_GUIDE.md)
- [Docker 部署指南](DOCKER_DEPLOY.md)
- [快速开始](QUICK_START.md)

## 🔐 生产环境建议

### 1. 使用固定版本标签

```yaml
services:
  sandbox-code-interpreter:
    # ✅ 推荐: 使用具体版本
    image: registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-v0.2.2
    
    # ❌ 不推荐: 使用 latest 标签
    # image: ....:latest
```

### 2. 配置资源限制

```yaml
services:
  mcp-server:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### 3. 设置重启策略

```yaml
services:
  mcp-server:
    restart: unless-stopped  # 或 always
```

### 4. 数据备份

```bash
# 备份数据卷
docker run --rm -v sandbox-code-interpreter-mcp-server_sandbox-workspace:/data -v $(pwd):/backup alpine tar czf /backup/workspace-backup.tar.gz -C /data .
```

---

**快速部署！🚀**
