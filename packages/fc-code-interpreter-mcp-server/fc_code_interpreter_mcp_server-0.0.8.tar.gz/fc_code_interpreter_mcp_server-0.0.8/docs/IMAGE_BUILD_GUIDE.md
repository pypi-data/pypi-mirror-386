# 镜像构建和推送指南

本指南介绍如何构建 Docker 镜像并推送到阿里云容器镜像服务。

## 🎯 快速开始

### 一键构建并推送

```bash
# 构建并推送镜像（自动使用 git 版本号）
make image
```

## 📋 可用命令

| 命令 | 说明 |
|------|------|
| `make image` | 构建并推送镜像到阿里云 |
| `make image-build` | 仅构建镜像（不推送） |
| `make image-push` | 推送已构建的镜像 |
| `make image-login` | 登录阿里云容器镜像服务 |
| `make image-info` | 显示镜像配置和版本信息 |

## 🔧 配置说明

### 默认配置

镜像会被推送到以下地址：

```
registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-${GIT_VERSION}
```

其中 `${GIT_VERSION}` 自动从 git 仓库获取：
- 如果有 tag: 使用 tag 名称
- 否则使用: commit hash (短格式)
- 如果有未提交的改动: 添加 `-dirty` 后缀

### 环境变量配置

你可以通过环境变量自定义配置：

```bash
# 阿里云镜像仓库地址
ALIYUN_REGISTRY=registry.cn-hangzhou.aliyuncs.com

# 命名空间
ALIYUN_NAMESPACE=dockerhacker

# 镜像名称
ALIYUN_IMAGE_NAME=sync

# 镜像前缀
ALIYUN_IMAGE_PREFIX=sandbox-code-interpreter-e2b-mcp
```

### 自定义示例

```bash
# 使用自定义命名空间
ALIYUN_NAMESPACE=mycompany make image

# 使用自定义镜像前缀
ALIYUN_IMAGE_PREFIX=mcp-server make image

# 完全自定义
ALIYUN_REGISTRY=registry.cn-shanghai.aliyuncs.com \
ALIYUN_NAMESPACE=myteam \
ALIYUN_IMAGE_NAME=mcp \
ALIYUN_IMAGE_PREFIX=server \
make image
```

## 🔐 登录阿里云

首次使用需要登录阿里云容器镜像服务：

### 方式 1: 使用 Make 命令

```bash
make image-login
```

### 方式 2: 直接使用 Docker

```bash
docker login registry.cn-hangzhou.aliyuncs.com
```

输入你的阿里云容器镜像服务凭证：
- 用户名: 阿里云账号全名
- 密码: 容器镜像服务密码（不是阿里云登录密码）

### 获取凭证

1. 登录阿里云控制台
2. 进入 **容器镜像服务** > **访问凭证**
3. 查看或重置密码

## 📦 构建流程

### 完整流程（make image）

```bash
make image
```

执行步骤：
1. ✅ 构建 Docker 镜像
   - 标记版本镜像: `...:sandbox-code-interpreter-e2b-mcp-${GIT_VERSION}`
   - 标记最新镜像: `...:sandbox-code-interpreter-e2b-mcp-latest`
   
2. ✅ 检查登录状态
   - 提示登录命令

3. ✅ 推送版本镜像
   - 推送 `${GIT_VERSION}` 标签

4. ✅ 推送最新镜像
   - 推送 `latest` 标签

### 分步操作

```bash
# 步骤 1: 仅构建
make image-build

# 步骤 2: 登录（如需要）
make image-login

# 步骤 3: 推送
make image-push
```

## 🔍 查看镜像信息

### 显示配置和版本

```bash
make image-info
```

输出示例：
```
镜像信息

配置:
  Registry:      registry.cn-hangzhou.aliyuncs.com
  Namespace:     dockerhacker
  Image Name:    sync
  Image Prefix:  sandbox-code-interpreter-e2b-mcp

版本信息:
  Git Version:   v2.2.0
  Git Commit:    c4d85cb

完整镜像地址:
  版本镜像:
    registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-v2.2.0

  最新镜像:
    registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest

拉取命令:
  docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-v2.2.0
```

### 查看构建的镜像

```bash
docker images | grep sandbox-code-interpreter-e2b-mcp
```

### 检查镜像标签

```bash
docker inspect registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest
```

## 🏷️ 版本管理

### Git Tag 版本

推荐使用 git tag 管理版本：

```bash
# 创建版本标签
git tag v2.2.1
git push origin v2.2.1

# 构建并推送（会使用 v2.2.1 作为版本号）
make image
```

生成的镜像：
- `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-v2.2.1`
- `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest`

### Commit Hash 版本

没有 tag 时使用 commit hash：

```bash
# 确保代码已提交
git commit -m "feat: 新功能"

# 构建（会使用 commit hash，如 c4d85cb）
make image
```

生成的镜像：
- `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-c4d85cb`
- `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest`

### Dirty 状态

如果有未提交的改动，版本号会添加 `-dirty` 后缀：

```bash
make image
```

生成的镜像：
- `registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-c4d85cb-dirty`

⚠️ **建议**: 推送到生产环境前先提交所有改动。

## 📥 拉取和使用镜像

### 拉取特定版本

```bash
docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-v2.2.0
```

### 拉取最新版本

```bash
docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest
```

### 在 docker-compose 中使用

```yaml
version: '3.8'

services:
  mcp-server:
    image: registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-v2.2.0
    ports:
      - "3000:3000"
    environment:
      - SANDBOX_URL=http://sandbox:8080
```

### 直接运行

```bash
docker run -d \
  -p 3000:3000 \
  -e SANDBOX_URL=http://sandbox:8080 \
  --name mcp-server \
  registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest
```

## 🐛 故障排查

### 问题 1: 登录失败

```bash
Error response from daemon: Get https://registry.cn-hangzhou.aliyuncs.com/v2/: unauthorized
```

**解决方案**:
```bash
# 重新登录
make image-login

# 或直接使用 docker login
docker login registry.cn-hangzhou.aliyuncs.com
```

### 问题 2: 推送失败（权限）

```bash
denied: requested access to the resource is denied
```

**解决方案**:
1. 确认命名空间存在
2. 确认有推送权限
3. 检查镜像仓库设置

### 问题 3: Git 版本获取失败

```bash
Git Version:   dev
```

**解决方案**:
```bash
# 确保在 git 仓库中
git status

# 提交代码
git add .
git commit -m "描述"

# 或创建 tag
git tag v1.0.0
```

### 问题 4: 构建失败

```bash
# 查看详细构建日志
docker build --no-cache --progress=plain .

# 清理并重试
docker system prune -af
make image-build
```

## 🔄 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Build and Push Docker Image

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Aliyun Registry
        run: |
          echo "${{ secrets.ALIYUN_DOCKER_PASSWORD }}" | \
          docker login registry.cn-hangzhou.aliyuncs.com \
            -u "${{ secrets.ALIYUN_DOCKER_USERNAME }}" \
            --password-stdin
      
      - name: Build and Push
        run: make image
```

### GitLab CI 示例

```yaml
build-image:
  stage: build
  script:
    - docker login registry.cn-hangzhou.aliyuncs.com -u $ALIYUN_USERNAME -p $ALIYUN_PASSWORD
    - make image
  only:
    - tags
```

## 📚 相关文档

- [Dockerfile](Dockerfile) - Docker 镜像定义
- [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md) - Docker 部署指南
- [Makefile](Makefile) - 所有构建命令

---

**Happy Building! 🏗️**
