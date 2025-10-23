.PHONY: help install dev run server inspector test clean docker-build docker-up docker-down docker-logs docker-restart

# 默认目标
.DEFAULT_GOAL := help

# 环境变量配置
SANDBOX_URL ?= http://localhost:5001

# Docker 配置
DOCKER_IMAGE_NAME ?= sandbox-mcp-server
DOCKER_IMAGE_TAG ?= latest

# 阿里云镜像仓库配置
ALIYUN_REGISTRY ?= registry.cn-hangzhou.aliyuncs.com
ALIYUN_NAMESPACE ?= dockerhacker
ALIYUN_IMAGE_NAME ?= sync
ALIYUN_IMAGE_PREFIX ?= sandbox-code-interpreter-e2b-mcp

# 获取 Git 版本号
GIT_VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
GIT_COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# 镜像源配置（国内用户使用阿里云镜像加速）
USE_ALIYUN_MIRROR ?= true

# 颜色输出
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
NC     := \033[0m # No Color

help: ## 显示帮助信息
	@echo "$(BLUE)Sandbox MCP Server - Makefile 命令$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "环境变量:"
	@echo "  SANDBOX_URL=$(SANDBOX_URL)"
	@echo ""

install: ## 安装依赖
	@echo "$(BLUE)安装 Python 依赖...$(NC)"
	uv install

dev: install ## 安装依赖并运行开发环境检查
	@echo "$(GREEN)✓ 开发环境准备完成$(NC)"
	@echo ""
	@echo "使用以下命令启动服务:"
	@echo "  $(YELLOW)make run$(NC)   - 启动 MCP server (stdio)"
	@echo "  $(YELLOW)make debug$(NC) - 调试模式 (使用 Inspector)"

run: ## 启动 MCP server (stdio 模式)
	@echo "$(BLUE)============================================$(NC)"
	@echo "$(GREEN)启动 Sandbox MCP Server$(NC)"
	@echo "$(BLUE)============================================$(NC)"
	@echo ""
	@echo "配置:"
	@echo "  Code Interpreter: $(SANDBOX_URL)"
	@echo "  Transport: stdio"
	@echo ""
	@echo "$(YELLOW)启动服务器...$(NC)"
	@echo ""
	uv run fc-code-interpreter-mcp-server --sandbox-url $(SANDBOX_URL)

server: run ## 启动 MCP server (别名)

run-with-inspector: ## 启动 MCP server 并自动打开 Inspector 调试
	@echo "$(BLUE)============================================$(NC)"
	@echo "$(GREEN)启动 Sandbox MCP Server + Inspector$(NC)"
	@echo "$(BLUE)============================================$(NC)"
	@echo ""
	@echo "配置:"
	@echo "  Code Interpreter: $(SANDBOX_URL)"
	@echo "  Transport: stdio"
	@echo ""
	@echo "$(YELLOW)启动 MCP Inspector...$(NC)"
	@echo ""
	SANDBOX_URL=$(SANDBOX_URL) npx @modelcontextprotocol/inspector uv run fc-code-interpreter-mcp-server

inspector: run-with-inspector ## 使用 MCP Inspector 调试 (别名)

test: ## 运行所有测试
	@echo "$(BLUE)运行测试套件...$(NC)"
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_e2b_integration.py
	@echo ""
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_simple_sandbox.py
	@echo ""
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_run_code.py
	@echo ""
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_mcp_server.py
	@echo ""
	@echo "$(GREEN)✓ 所有测试完成$(NC)"

test-integration: ## 运行 E2B 集成测试
	@echo "$(BLUE)运行 E2B 集成测试...$(NC)"
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_e2b_integration.py

test-sandbox: ## 运行 Sandbox 测试
	@echo "$(BLUE)运行 Sandbox 测试...$(NC)"
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_simple_sandbox.py

test-mcp: ## 运行 MCP Server 测试
	@echo "$(BLUE)运行 MCP Server 测试...$(NC)"
	@SANDBOX_URL=$(SANDBOX_URL) uv run python tests/test_mcp_server.py

clean: ## 清理临时文件
	@echo "$(BLUE)清理临时文件...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf build dist 2>/dev/null || true
	@echo "$(GREEN)✓ 清理完成$(NC)"

build: ## 构建 Python 包
	@echo "$(BLUE)构建 Python 包...$(NC)"
	poetry build
	@echo "$(GREEN)✓ 构建完成$(NC)"

publish: build ## 发布到 PyPI
	@echo "$(BLUE)发布到 PyPI...$(NC)"
	poetry publish
	@echo "$(GREEN)✓ 发布完成$(NC)"

# 命令别名
start: run ## 快速启动 MCP server (别名)
debug: run-with-inspector ## 调试 MCP server (别名)

# Docker 命令
docker-build: ## 构建 Docker 镜像
	@echo "$(BLUE)构建 Docker 镜像...$(NC)"
	docker build --build-arg USE_ALIYUN_MIRROR=$(USE_ALIYUN_MIRROR) -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) .
	@echo "$(GREEN)✓ 镜像构建完成: $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)$(NC)"

docker-up: ## 启动 Docker Compose 服务 (包含 sandbox 和 MCP server)
	@echo "$(BLUE)启动 Docker Compose 服务...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(GREEN)✓ 服务已启动$(NC)"
	@echo ""
	@echo "服务访问地址:"
	@echo "  $(YELLOW)Sandbox:$(NC)    http://localhost:5001"
	@echo "  $(YELLOW)MCP Server:$(NC) http://localhost:3000/sse"
	@echo ""
	@echo "查看日志: $(YELLOW)make docker-logs$(NC)"
	@echo "查看状态: $(YELLOW)docker-compose ps$(NC)"

docker-down: ## 停止并删除 Docker Compose 服务
	@echo "$(BLUE)停止 Docker Compose 服务...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ 服务已停止$(NC)"

docker-restart: ## 重启 Docker Compose 服务
	@echo "$(BLUE)重启 Docker Compose 服务...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ 服务已重启$(NC)"

docker-logs: ## 查看 Docker Compose 服务日志
	@echo "$(BLUE)查看服务日志 (Ctrl+C 退出)...$(NC)"
	@echo ""
	docker-compose logs -f

docker-logs-mcp: ## 查看 MCP Server 日志
	@echo "$(BLUE)查看 MCP Server 日志...$(NC)"
	docker-compose logs -f mcp-server

docker-logs-sandbox: ## 查看 Sandbox 日志
	@echo "$(BLUE)查看 Sandbox 日志...$(NC)"
	docker-compose logs -f sandbox-code-interpreter

docker-ps: ## 查看 Docker Compose 服务状态
	@docker-compose ps

docker-shell-mcp: ## 进入 MCP Server 容器
	@echo "$(BLUE)进入 MCP Server 容器...$(NC)"
	docker-compose exec mcp-server /bin/bash

docker-clean: docker-down ## 清理 Docker 资源 (容器、镜像、卷)
	@echo "$(BLUE)清理 Docker 资源...$(NC)"
	docker-compose down -v --rmi local
	@echo "$(GREEN)✓ 清理完成$(NC)"

# 更多别名
up: docker-up ## 启动 Docker 服务 (别名)
down: docker-down ## 停止 Docker 服务 (别名)
logs: docker-logs ## 查看日志 (别名)

# 镜像构建和推送
image: ## 构建并推送镜像到阿里云容器镜像服务
	@echo "$(BLUE)============================================$(NC)"
	@echo "$(GREEN)构建并推送 Docker 镜像到阿里云$(NC)"
	@echo "$(BLUE)============================================$(NC)"
	@echo ""
	@echo "配置信息:"
	@echo "  Git Version:   $(GIT_VERSION)"
	@echo "  Git Commit:    $(GIT_COMMIT)"
	@echo "  Registry:      $(ALIYUN_REGISTRY)"
	@echo "  Image:         $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
	@echo ""
	@echo "$(YELLOW)步骤 1/4: 构建 Docker 镜像...$(NC)"
	docker build \
		--build-arg GIT_VERSION=$(GIT_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg USE_ALIYUN_MIRROR=$(USE_ALIYUN_MIRROR) \
		-t $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION) \
		-t $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest \
		.
	@echo ""
	@echo "$(GREEN)✓ 镜像构建完成$(NC)"
	@echo ""
	@echo "$(YELLOW)步骤 2/4: 登录阿里云容器镜像服务...$(NC)"
	@echo "请确保已配置阿里云 Docker 登录凭证"
	@echo "如需登录，请运行: docker login $(ALIYUN_REGISTRY)"
	@echo ""
	@echo "$(YELLOW)步骤 3/4: 推送版本镜像 $(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)...$(NC)"
	docker push $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)
	@echo ""
	@echo "$(GREEN)✓ 版本镜像推送完成$(NC)"
	@echo ""
	@echo "$(YELLOW)步骤 4/4: 推送 latest 镜像...$(NC)"
	docker push $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest
	@echo ""
	@echo "$(GREEN)============================================$(NC)"
	@echo "$(GREEN)✓ 镜像推送完成！$(NC)"
	@echo "$(GREEN)============================================$(NC)"
	@echo ""
	@echo "镜像地址:"
	@echo "  $(YELLOW)版本镜像:$(NC) $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
	@echo "  $(YELLOW)最新镜像:$(NC) $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest"
	@echo ""
	@echo "拉取镜像:"
	@echo "  docker pull $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"

image-build: ## 仅构建镜像（不推送）
	@echo "$(BLUE)构建 Docker 镜像...$(NC)"
	@echo ""
	@echo "配置信息:"
	@echo "  Git Version:   $(GIT_VERSION)"
	@echo "  Git Commit:    $(GIT_COMMIT)"
	@echo "  Image Tag:     $(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
	@echo ""
	docker build \
		--build-arg GIT_VERSION=$(GIT_VERSION) \
		--build-arg GIT_COMMIT=$(GIT_COMMIT) \
		--build-arg USE_ALIYUN_MIRROR=$(USE_ALIYUN_MIRROR) \
		-t $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION) \
		-t $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest \
		.
	@echo ""
	@echo "$(GREEN)✓ 镜像构建完成$(NC)"
	@echo ""
	@echo "本地镜像:"
	@echo "  $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
	@echo "  $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest"

image-push: ## 推送已构建的镜像
	@echo "$(BLUE)推送镜像到阿里云...$(NC)"
	@echo ""
	@echo "$(YELLOW)推送版本镜像...$(NC)"
	docker push $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)
	@echo ""
	@echo "$(YELLOW)推送 latest 镜像...$(NC)"
	docker push $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest
	@echo ""
	@echo "$(GREEN)✓ 推送完成$(NC)"

image-login: ## 登录阿里云容器镜像服务
	@echo "$(BLUE)登录阿里云容器镜像服务...$(NC)"
	@echo ""
	@echo "Registry: $(ALIYUN_REGISTRY)"
	@echo ""
	@echo "请输入阿里云容器镜像服务凭证:"
	docker login $(ALIYUN_REGISTRY)

image-info: ## 显示镜像信息
	@echo "$(BLUE)镜像信息$(NC)"
	@echo ""
	@echo "配置:"
	@echo "  Registry:      $(ALIYUN_REGISTRY)"
	@echo "  Namespace:     $(ALIYUN_NAMESPACE)"
	@echo "  Image Name:    $(ALIYUN_IMAGE_NAME)"
	@echo "  Image Prefix:  $(ALIYUN_IMAGE_PREFIX)"
	@echo ""
	@echo "版本信息:"
	@echo "  Git Version:   $(GIT_VERSION)"
	@echo "  Git Commit:    $(GIT_COMMIT)"
	@echo ""
	@echo "完整镜像地址:"
	@echo "  $(YELLOW)版本镜像:$(NC)"
	@echo "    $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
	@echo ""
	@echo "  $(YELLOW)最新镜像:$(NC)"
	@echo "    $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-latest"
	@echo ""
	@echo "拉取命令:"
	@echo "  docker pull $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(ALIYUN_IMAGE_NAME):$(ALIYUN_IMAGE_PREFIX)-$(GIT_VERSION)"
