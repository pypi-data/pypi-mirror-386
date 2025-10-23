# Docker 部署指南

本指南介绍如何使用 Docker 和 Docker Compose 部署 Sandbox MCP Server。

## 🚀 快速开始

### 方式 1: 使用 Docker Compose（推荐）

一键启动所有服务（Sandbox + MCP Server）：

```bash
# 启动所有服务
make docker-up

# 或直接使用 docker-compose
docker-compose up -d
```

### 方式 2: 只构建 MCP Server 镜像

```bash
# 构建镜像
make docker-build

# 或直接使用 docker
docker build -t sandbox-mcp-server:latest .
```

## 📦 架构说明

Docker Compose 启动两个服务：

1. **sandbox-code-interpreter** - 代码执行引擎（数据层）
   - 端口: 5001 (映射到容器内的 8080)
   - 健康检查: `/health` 端点
   
2. **mcp-server** - MCP 协议服务器（控制层）
   - 端口: 3000
   - SSE 端点: `http://localhost:3000/sse`
   - 消息端点: `http://localhost:3000/messages`
   - 依赖: sandbox-code-interpreter

## 🔧 环境变量配置

### Sandbox 配置

```yaml
SANDBOX_ENV: production
SANDBOX_HOST: 0.0.0.0
SANDBOX_PORT: 8080
SANDBOX_DEBUG: false
SANDBOX_LOG_LEVEL: info
SANDBOX_WORKSPACE_DIR: /workspace
SANDBOX_MAX_CONTEXTS: 100
```

### MCP Server 配置

```yaml
SANDBOX_URL: http://sandbox-code-interpreter:8080
MCP_HOST: 0.0.0.0
MCP_PORT: 3000
LOG_LEVEL: INFO
```

## 📋 Make 命令

### 基本操作

```bash
# 构建镜像
make docker-build

# 启动服务
make docker-up
# 或简写
make up

# 停止服务
make docker-down
# 或简写
make down

# 重启服务
make docker-restart
```

### 日志查看

```bash
# 查看所有服务日志
make docker-logs
# 或简写
make logs

# 只查看 MCP Server 日志
make docker-logs-mcp

# 只查看 Sandbox 日志
make docker-logs-sandbox
```

### 服务管理

```bash
# 查看服务状态
make docker-ps
# 或
docker-compose ps

# 进入 MCP Server 容器
make docker-shell-mcp

# 清理所有资源（容器、镜像、卷）
make docker-clean
```

## 🔍 服务验证

### 1. 检查服务状态

```bash
docker-compose ps
```

预期输出：
```
NAME                       IMAGE                             STATUS
sandbox-code-interpreter   sandbox-code-interpreter:latest   Up (healthy)
sandbox-mcp-server         sandbox-mcp-server:latest         Up (healthy)
```

### 2. 测试 Sandbox

```bash
curl http://localhost:5001/health
```

预期响应：
```json
{"status":"healthy"}
```

### 3. 测试 MCP Server SSE 端点

```bash
timeout 2 curl -I http://localhost:3000/sse
```

预期响应：
```
HTTP/1.1 200 OK
content-type: text/event-stream; charset=utf-8
...
```

### 4. 使用 MCP Inspector 测试

```bash
npx @modelcontextprotocol/inspector http://localhost:3000/sse
```

## 📊 健康检查

### Sandbox 健康检查

```bash
docker inspect sandbox-code-interpreter \
  --format='{{.State.Health.Status}}'
```

### MCP Server 健康检查

```bash
docker inspect sandbox-mcp-server \
  --format='{{.State.Health.Status}}'
```

## 🐛 故障排查

### 问题 1: 端口冲突

```bash
# 检查端口占用
lsof -i :5001
lsof -i :3000

# 修改端口映射
# 编辑 docker-compose.yml 中的 ports 配置
```

### 问题 2: 容器无法启动

```bash
# 查看详细日志
docker-compose logs sandbox-code-interpreter
docker-compose logs mcp-server

# 查看容器状态
docker-compose ps
docker inspect <container_name>
```

### 问题 3: MCP Server 无法连接 Sandbox

```bash
# 确认 Sandbox 健康
curl http://localhost:5001/health

# 检查网络连接
docker-compose exec mcp-server curl http://sandbox-code-interpreter:8080/health

# 查看 MCP Server 日志
docker-compose logs mcp-server
```

### 问题 4: 构建失败

```bash
# 清理旧镜像
docker system prune -a

# 重新构建（无缓存）
docker-compose build --no-cache

# 或
docker build --no-cache -t sandbox-mcp-server:latest .
```

## 🔄 更新部署

### 更新代码后重新部署

```bash
# 停止服务
make docker-down

# 重新构建
make docker-build

# 启动服务
make docker-up
```

### 快速重启（不重新构建）

```bash
make docker-restart
```

## 📁 数据持久化

Docker Compose 使用命名卷持久化数据：

- **sandbox-workspace**: Sandbox 工作目录
- **sandbox-logs**: Sandbox 日志

查看卷：
```bash
docker volume ls | grep sandbox
```

清理卷（⚠️ 会删除所有数据）：
```bash
docker-compose down -v
```

## 🌐 网络配置

服务之间通过 `sandbox-net` 网络通信：

```bash
# 查看网络
docker network inspect sandbox-code-interpreter-mcp-server_sandbox-net

# 查看网络中的容器
docker network inspect sandbox-code-interpreter-mcp-server_sandbox-net \
  --format='{{range .Containers}}{{.Name}} {{end}}'
```

## 🔒 生产环境建议

1. **使用环境变量文件**
   ```bash
   # 创建 .env 文件
   cp .env.example .env
   # 编辑配置
   vi .env
   ```

2. **启用 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书
   - 限制直接访问

3. **资源限制**
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

4. **监控和日志**
   - 配置日志轮转
   - 使用 Prometheus + Grafana 监控
   - 设置告警规则

5. **备份策略**
   - 定期备份数据卷
   - 保存镜像版本
   - 记录配置变更

## 📚 相关文档

- [README.md](README.md) - 项目总览
- [QUICK_START.md](QUICK_START.md) - 快速启动指南
- [Dockerfile](Dockerfile) - Docker 镜像定义
- [docker-compose.yml](docker-compose.yml) - 服务编排配置

---

**Happy Dockering! 🐳**

## 🌏 国内用户加速

### 阿里云 APT 镜像源

默认情况下，Dockerfile 使用阿里云的 Debian APT 镜像源来加速国内用户的构建速度。

这会自动将以下源替换为阿里云镜像：
- `deb.debian.org` → `mirrors.aliyun.com`
- `security.debian.org` → `mirrors.aliyun.com`

### 禁用阿里云镜像（海外用户）

如果你在海外或不需要使用阿里云镜像，可以禁用它：

```bash
# 方式 1: 使用环境变量
USE_ALIYUN_MIRROR=false make docker-build

# 方式 2: 直接使用 docker build
docker build --build-arg USE_ALIYUN_MIRROR=false -t sandbox-mcp-server:latest .

# 方式 3: 修改 Makefile 默认值
# 编辑 Makefile，将 USE_ALIYUN_MIRROR 默认值改为 false
USE_ALIYUN_MIRROR ?= false
```

### 验证镜像源配置

构建镜像后，可以检查是否使用了阿里云镜像：

```bash
# 进入容器检查
docker run --rm -it sandbox-mcp-server:latest cat /etc/apt/sources.list.d/debian.sources | grep -E "deb.debian.org|mirrors.aliyun.com"
```

