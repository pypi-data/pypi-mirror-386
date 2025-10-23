# E2B on Aliyun Function Compute SDK

This is a modified version of the E2B SDK that works with Aliyun Function Compute infrastructure for secure, isolated code execution.

## Overview

This package provides sandbox code execution capabilities using Aliyun Function Compute as the backend, maintaining compatibility with the E2B SDK API.

## Features

- **Secure Sandbox Execution**: Run code in isolated Function Compute environments
- **Multi-language Support**: Python, JavaScript, and other languages
- **E2B API Compatibility**: Maintains similar API to the original E2B SDK
- **Context Management**: Isolated execution contexts for state management
- **File System Operations**: Read/write files within sandboxes

## Installation

This package is included as an internal dependency in the AgentRun MCP Server project.

## Usage

```python
from e2b_on_fc import Sandbox

# Create a sandbox (debug mode for local testing)
sandbox = Sandbox(debug=True)

# Execute Python code
execution = sandbox.run_code("print('Hello, World!')")
print(execution.logs)

# Create a context for stateful execution
context = sandbox.create_code_context()
sandbox.run_code("x = 100", context=context)
result = sandbox.run_code("print(x)", context=context)
```

## Configuration

For local development:
- Set `LOCAL_ENDPOINT` environment variable to point to your local code interpreter service
- Default: `http://localhost:5001`

For production with Aliyun Function Compute:
- `ALIBABA_CLOUD_ACCESS_KEY_ID`: Your Aliyun access key ID
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: Your Aliyun access key secret
- `ENDPOINT`: Function Compute endpoint (format: `{account_id}.{region}.fc.aliyuncs.com`)

## Source

Based on: https://github.com/aliyun-fc/e2b-on-aliyun-fc

## License

See the main project LICENSE file.
