# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is an AgentRun MCP (Model Context Protocol) Server, which provides secure code interpreting capabilities through AgentRun Code Interpreter.

The Python server exposes 4 MCP tools for code execution with context management and session pooling.

## Project Structure

```
.
├── mcp_server/                # Python MCP server implementation
│   ├── __init__.py            # Package entry point
│   └── server.py              # Main server logic
├── agentrun-ci-sdk-preview/   # AgentRun SDK (preview)
├── docs/                      # Documentation
│   ├── README.md
│   ├── QUICK_START.md
│   ├── MIGRATION_GUIDE.md
│   └── TOOLS_API.md
├── pyproject.toml             # Python package configuration
├── poetry.lock                # Poetry dependencies lock
├── uv.lock                    # UV dependencies lock
├── .env.example               # Environment variables template
└── README.md                  # Project documentation
```

## Development Commands

```bash
# Install dependencies
uv install

# Start local sandbox
docker-compose up -d

# Run server (SSE mode)
make run

# Run with Inspector for debugging
make debug

# Run tests
make test

# View all available commands
make help
```

## Architecture

### MCP Server Pattern

The Python implementation uses E2B SDK with SSE transport:

1. **Server Initialization**: Creates an MCP server with SSE (HTTP) transport
2. **E2B Integration**: Connects to E2B sandbox (local Docker or AgentRun cloud)
3. **Context Management**: User-managed execution contexts for isolated code execution
4. **Tool Registration**: Registers 4 MCP tools with JSON schema validation:
   - `run_code` - Execute code in isolated contexts (Python/JavaScript)
   - `create_context` - Create persistent execution contexts
   - `stop_context` - Stop and cleanup contexts
   - `list_contexts` - List all active contexts with metadata
5. **SSE Transport**: HTTP-based streaming for remote access and debugging

### Key Components

- **E2B SDK**: Secure sandbox execution via e2b-on-fc
- **SSE Transport**: HTTP streaming using Starlette + Uvicorn
- **Context Registry**: Manages execution context lifecycle and state
- **MCP SDK**: Handles Model Context Protocol communication
- **Schema Validation**: Uses Pydantic for type-safe input/output

### Configuration

#### Local Sandbox (Development)

```bash
# Sandbox configuration
SANDBOX_URL=http://localhost:5001   # Local sandbox endpoint

# Server configuration
MCP_HOST=0.0.0.0                     # Bind address
MCP_PORT=3000                        # Server port
LOG_LEVEL=INFO                       # Logging level
```

#### AgentRun Cloud (Production)

```bash
AGENTRUN_ACCESS_KEY_ID=your_key
AGENTRUN_ACCESS_KEY_SECRET=your_secret
AGENTRUN_ACCOUNT_ID=your_account_id
AGENTRUN_REGION=cn-hangzhou
```

Load via `.env` file or environment variables.

## Publishing

### Version Management

Update version in `pyproject.toml`:

```bash
# Manually edit version in pyproject.toml
# Then build and publish
poetry build
poetry publish

# Or use bump2version
pip install bump2version
bump2version patch  # or minor, or major
```

### Automated Publishing

Publishing to PyPI is automated via GitHub Actions when pushing version tags:

```bash
git tag v2.2.1
git push origin v2.2.1
```

Required GitHub secret: `PYPI_TOKEN`

## Development Notes

- **Package Location**: Python package is in the root directory
- **Publishing**: Python package publishes to PyPI via Git tags
- **MCP Communication**: SSE transport via HTTP (port 3000 by default)
- **Debugging**: Use `make debug` to start with MCP Inspector
- **Startup Time**: Local sandbox starts in ~3-5 seconds
- **Context Management**: User-managed contexts with persistent state
- **Log Files**: Server logs are stored in `/tmp/mcp-server.log` during debug mode

## Testing

### Using Make Commands

```bash
# Run all tests
make test

# Test with Inspector (interactive)
make debug
```

### Manual Testing Workflow

1. Start sandbox: `docker-compose up -d`
2. Start server: `make debug`
3. In MCP Inspector:
   - **Create Context**: `create_context(name="test", language="python")`
   - **Run Code**: `run_code(code="x = 100\nprint(x)", context_id="ctx-xxx")`
   - **List Contexts**: `list_contexts()`
   - **Stop Context**: `stop_context(context_id="ctx-xxx")`

### Debugging Tips

- View server logs: `tail -f /tmp/mcp-server.log`
- Check sandbox health: `curl http://localhost:5001/health`
- Test SSE endpoint: `timeout 2 curl -I http://localhost:3000/sse`
## Environment Requirements

- **Python**: Python 3.10+, uv package manager
- **AgentRun Credentials**: Access key ID, secret, account ID, and region required
- **Documentation**: See `docs/` directory for detailed guides
