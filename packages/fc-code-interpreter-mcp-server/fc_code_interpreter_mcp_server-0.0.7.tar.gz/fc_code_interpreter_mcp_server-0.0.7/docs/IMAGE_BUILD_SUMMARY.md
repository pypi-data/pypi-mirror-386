# 镜像构建功能总结

## ✅ 完成的工作

### 1. 添加了镜像构建命令

在 Makefile 中添加了以下命令：

| 命令 | 功能 |
|------|------|
| `make image` | 一键构建并推送镜像到阿里云 |
| `make image-build` | 仅构建镜像（不推送） |
| `make image-push` | 推送已构建的镜像 |
| `make image-login` | 登录阿里云容器镜像服务 |
| `make image-info` | 显示镜像配置和版本信息 |

### 2. 自动版本管理

- ✅ 自动从 git 获取版本号
- ✅ 支持 git tag 作为版本
- ✅ 支持 commit hash 作为版本
- ✅ 检测未提交改动（添加 `-dirty` 后缀）

### 3. 镜像标签策略

每次构建会生成两个标签：

1. **版本标签**: `sandbox-code-interpreter-e2b-mcp-${GIT_VERSION}`
2. **最新标签**: `sandbox-code-interpreter-e2b-mcp-latest`

### 4. 完整文档

- ✅ [IMAGE_BUILD_GUIDE.md](IMAGE_BUILD_GUIDE.md) - 373 行完整指南
- ✅ 包含登录、构建、推送、故障排查、CI/CD 集成等

## 🎯 镜像地址格式

```
registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-${VERSION}
```

### 组成部分

- **Registry**: `registry.cn-hangzhou.aliyuncs.com`
- **Namespace**: `dockerhacker`
- **Image Name**: `sync`
- **Tag Prefix**: `sandbox-code-interpreter-e2b-mcp`
- **Version**: 从 git 自动获取

## 🚀 使用示例

### 查看当前版本信息

```bash
make image-info
```

输出:
```
镜像信息

配置:
  Registry:      registry.cn-hangzhou.aliyuncs.com
  Namespace:     dockerhacker
  Image Name:    sync
  Image Prefix:  sandbox-code-interpreter-e2b-mcp

版本信息:
  Git Version:   c4d85cb
  Git Commit:    c4d85cb

完整镜像地址:
  版本镜像:
    registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-c4d85cb

  最新镜像:
    registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest
```

### 构建并推送

```bash
# 1. 登录（首次）
make image-login

# 2. 构建并推送
make image
```

### 分步操作

```bash
# 仅构建
make image-build

# 推送
make image-push
```

## 🔧 自定义配置

### 使用环境变量

```bash
# 自定义命名空间
ALIYUN_NAMESPACE=mycompany make image

# 自定义镜像前缀
ALIYUN_IMAGE_PREFIX=mcp-server make image

# 完全自定义
ALIYUN_REGISTRY=registry.cn-shanghai.aliyuncs.com \
ALIYUN_NAMESPACE=myteam \
ALIYUN_IMAGE_NAME=mcp \
ALIYUN_IMAGE_PREFIX=server \
make image
```

### 编辑 Makefile

直接修改 Makefile 中的默认值：

```makefile
ALIYUN_REGISTRY ?= registry.cn-hangzhou.aliyuncs.com
ALIYUN_NAMESPACE ?= dockerhacker
ALIYUN_IMAGE_NAME ?= sync
ALIYUN_IMAGE_PREFIX ?= sandbox-code-interpreter-e2b-mcp
```

## 📝 版本管理最佳实践

### 1. 使用 Git Tag 发布版本

```bash
# 开发完成后
git add .
git commit -m "feat: 新功能"

# 创建版本标签
git tag v2.2.1
git push origin v2.2.1

# 构建发布镜像
make image
```

生成镜像：
- `...:sandbox-code-interpreter-e2b-mcp-v2.2.1`
- `...:sandbox-code-interpreter-e2b-mcp-latest`

### 2. 开发版本

```bash
# 提交代码
git commit -m "wip: 开发中"

# 构建开发镜像
make image-build  # 仅构建，不推送
```

生成镜像：
- `...:sandbox-code-interpreter-e2b-mcp-${COMMIT_HASH}`

### 3. 避免 Dirty 版本

❌ **不推荐**（有未提交改动）:
```bash
# 修改了文件但未提交
make image
# 生成: ...:sandbox-code-interpreter-e2b-mcp-c4d85cb-dirty
```

✅ **推荐**:
```bash
# 先提交
git add .
git commit -m "fix: 修复问题"

# 再构建
make image
# 生成: ...:sandbox-code-interpreter-e2b-mcp-${NEW_COMMIT}
```

## 🔍 验证镜像

### 检查本地镜像

```bash
docker images | grep sandbox-code-interpreter-e2b-mcp
```

### 检查镜像标签

```bash
docker inspect registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest | grep -A 5 Labels
```

### 拉取并测试

```bash
# 拉取镜像
docker pull registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest

# 运行测试
docker run --rm \
  -e SANDBOX_URL=http://host.docker.internal:5001 \
  -p 3000:3000 \
  registry.cn-hangzhou.aliyuncs.com/dockerhacker/sync:sandbox-code-interpreter-e2b-mcp-latest
```

## 📦 更新的文件

1. ✅ **Makefile** - 添加镜像构建命令和配置
2. ✅ **Dockerfile** - 添加版本标签（ARG 和 LABEL）
3. ✅ **IMAGE_BUILD_GUIDE.md** - 完整构建指南（新建）
4. ✅ **IMAGE_BUILD_SUMMARY.md** - 功能总结（本文件）
5. ✅ **README.md** - 添加文档链接

## 🎯 下一步

### 1. 测试构建

```bash
# 查看版本信息
make image-info

# 仅构建（测试）
make image-build

# 检查镜像
docker images | grep sandbox-code-interpreter-e2b-mcp
```

### 2. 登录阿里云

```bash
make image-login
```

### 3. 构建并推送

```bash
# 确保代码已提交
git status

# 构建并推送
make image
```

### 4. 创建 Git 提交

```bash
git add Makefile Dockerfile IMAGE_BUILD_GUIDE.md IMAGE_BUILD_SUMMARY.md README.md
git commit -m "feat: 添加阿里云镜像构建和推送功能

- 添加 make image 命令自动构建并推送镜像
- 支持自动从 git 获取版本号
- 添加完整的镜像构建指南
- 支持自定义镜像仓库配置"
```

## 📚 相关文档

- [IMAGE_BUILD_GUIDE.md](IMAGE_BUILD_GUIDE.md) - 完整构建指南
- [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md) - Docker 部署指南
- [Makefile](Makefile) - 所有命令定义
- [Dockerfile](Dockerfile) - 镜像定义

---

**Ready to Build and Push! 🚀**
