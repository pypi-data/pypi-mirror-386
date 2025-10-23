# Dockerfile for Sandbox MCP Server
FROM python:3.12-slim

# Build arguments for version tracking
ARG GIT_VERSION=dev
ARG GIT_COMMIT=unknown
ARG BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

# Build argument to control mirror usage (default: true for China users)
ARG USE_ALIYUN_MIRROR=true

LABEL maintainer="Sandbox Team"
LABEL description="Code Interpreter MCP Server with E2B integration"
LABEL version="${GIT_VERSION}"
LABEL git.commit="${GIT_COMMIT}"
LABEL build.date="${BUILD_DATE}"

# Set working directory
WORKDIR /app

# Configure Aliyun apt mirrors for faster downloads in China
# To disable: docker build --build-arg USE_ALIYUN_MIRROR=false .
RUN if [ "$USE_ALIYUN_MIRROR" = "true" ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; \
    fi

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./
COPY e2b_on_fc ./e2b_on_fc
COPY README.md ./
COPY mcp_server ./mcp_server

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Create non-root user
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

USER mcp

# Environment variables with defaults
ENV SANDBOX_URL=http://sandbox-code-interpreter:8080 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=3000 \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1

# Expose MCP server port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${MCP_PORT}/sse || exit 1

# Run the MCP server
# Use shell form to allow environment variable expansion
CMD uv run sandbox-mcp-server --sandbox-url ${SANDBOX_URL} --host ${MCP_HOST} --port ${MCP_PORT}
