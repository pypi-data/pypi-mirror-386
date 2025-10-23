#!/bin/bash
# Load environment variables from .env file
set -a
source .env
set +a

# Run MCP Inspector
npx @modelcontextprotocol/inspector uv --directory . run agentrun-mcp-server
