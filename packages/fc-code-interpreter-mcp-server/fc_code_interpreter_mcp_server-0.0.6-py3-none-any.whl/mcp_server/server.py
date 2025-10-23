"""Code Interpreter MCP Server with E2B SDK Integration.

Features:
- E2B Sandbox with session management
- Multi-language support (Python and JavaScript)
- Explicit context management
- 4 MCP tools: run_code, create_context, stop_context, list_contexts
"""

import os
import sys
import json
import logging
import time
import uuid
import argparse
from collections.abc import Sequence
from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel, ValidationError, Field

# Load environment variables - try both current dir and parent dir
from pathlib import Path
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path if env_path.exists() else None)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sandbox-mcp-server")

# Import E2B on FC SDK
try:
    from e2b_on_fc import Sandbox, Context, Execution
    E2B_AVAILABLE = True
except ImportError as e:
    logger.warning(f"E2B on FC SDK not available: {e}")
    E2B_AVAILABLE = False
    Sandbox = None
    Context = None
    Execution = None


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ContextInfo:
    """Context information."""
    context_id: str
    name: str
    language: str  # "python" or "javascript"
    description: str
    created_at: float
    last_used: float
    status: str = "active"


# ============================================================================
# Tool Schemas
# ============================================================================

class RunCodeSchema(BaseModel):
    """Schema for run_code tool."""
    code: str = Field(..., description="Python or JavaScript code to execute")
    context_id: str = Field(..., description="Context ID (required)")


class CreateContextSchema(BaseModel):
    """Schema for create_context tool."""
    language: str = Field(..., description="Programming language: python or javascript")
    name: Optional[str] = Field("", description="Context name (optional)")
    description: Optional[str] = Field("", description="Context description (optional)")


class StopContextSchema(BaseModel):
    """Schema for stop_context tool."""
    context_id: str = Field(..., description="Context ID to stop")


# ============================================================================
# Global State
# ============================================================================

# Context registry: stores all active contexts
context_registry: dict[str, ContextInfo] = {}

# Server start time
server_start_time = time.time()

# Global state for E2B Sandbox
e2b_sandbox: Optional['Sandbox'] = None
e2b_contexts: dict[str, 'Context'] = {}  # Maps context_id to E2B Context objects


# ============================================================================
# MCP Server
# ============================================================================

app = Server("sandbox-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="run_code",
            description="Run Python or JavaScript code in sandbox. context_id is required.",
            inputSchema=RunCodeSchema.model_json_schema()
        ),
        Tool(
            name="create_context",
            description="Create a new isolated code execution context. Supports Python and JavaScript.",
            inputSchema=CreateContextSchema.model_json_schema()
        ),
        Tool(
            name="stop_context",
            description="Stop and cleanup a context, releasing resources.",
            inputSchema=StopContextSchema.model_json_schema()
        ),
        Tool(
            name="list_contexts",
            description="List all active execution contexts.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle MCP tool calls."""
    
    try:
        if name == "run_code":
            return await handle_run_code(arguments)
        elif name == "create_context":
            return await handle_create_context(arguments)
        elif name == "stop_context":
            return await handle_stop_context(arguments)
        elif name == "list_contexts":
            return await handle_list_contexts(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except ValidationError as e:
        error_msg = f"Invalid arguments: {e}"
        logger.error(error_msg)
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": error_msg, "code": "INVALID_PARAMS"}, indent=2)
            )
        ]
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({"error": error_msg, "code": "EXECUTION_FAILED"}, indent=2)
            )
        ]


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_run_code(arguments: Any) -> Sequence[TextContent]:
    """Handle run_code tool."""
    # Validate arguments
    args = RunCodeSchema.model_validate(arguments)
    
    # Check if context exists
    if args.context_id not in context_registry:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Context not found: {args.context_id}",
                    "code": "CONTEXT_NOT_FOUND"
                }, indent=2)
            )
        ]
    
    # Get context info
    context = context_registry[args.context_id]
    
    # Check if E2B sandbox is available
    if not E2B_AVAILABLE or not e2b_sandbox:
        # Fallback to mock execution
        logger.warning("E2B Sandbox not available, using mock execution")
        result = {
            "stdout": f"[MOCK] Code executed in {context.language} context\n",
            "stderr": "",
            "success": True,
            "execution_time": 0.123
        }
        context.last_used = time.time()
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
    
    try:
        # Execute code via E2B SDK
        logger.info(f"Executing code in context {args.context_id} (language: {context.language})")
        
        # Get E2B context object
        e2b_context = e2b_contexts.get(args.context_id)
        
        # Execute code with context
        start_time = time.time()
        if e2b_context:
            execution = e2b_sandbox.run_code(
                code=args.code,
                context=e2b_context
            )
        else:
            # Execute without context (create new one)
            execution = e2b_sandbox.run_code(
                code=args.code,
                language=context.language
            )
        execution_time = time.time() - start_time
        
        # Build result from E2B execution
        # Note: execution.logs.stdout and stderr are lists of strings, not objects
        result = {
            "stdout": "".join(execution.logs.stdout) if execution.logs and execution.logs.stdout else "",
            "stderr": "".join(execution.logs.stderr) if execution.logs and execution.logs.stderr else "",
            "success": execution.error is None,
            "execution_time": execution_time,
            "error": str(execution.error) if execution.error else None
        }
        
        # Update last_used time
        context.last_used = time.time()
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
    
    except Exception as e:
        logger.error(f"Code execution failed: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "code": "EXECUTION_FAILED"
                }, indent=2)
            )
        ]


async def handle_create_context(arguments: Any) -> Sequence[TextContent]:
    """Handle create_context tool."""
    # Validate arguments
    args = CreateContextSchema.model_validate(arguments)
    
    # Validate language
    if args.language not in ["python", "javascript"]:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unsupported language: {args.language}. Must be 'python' or 'javascript'",
                    "code": "INVALID_LANGUAGE"
                }, indent=2)
            )
        ]
    
    # Generate context_id
    context_id = f"ctx-{uuid.uuid4()}"
    
    # Generate name if not provided
    context_name = args.name if args.name else f"{args.language}-{context_id[:8]}"
    
    # Create context in E2B sandbox if available
    if E2B_AVAILABLE and e2b_sandbox:
        try:
            # Create E2B context
            e2b_context = e2b_sandbox.create_code_context()
            e2b_contexts[context_id] = e2b_context
            logger.info(f"Created {args.language} context in E2B: {context_id}")
        except Exception as e:
            logger.warning(f"Failed to create context in E2B: {e}", exc_info=True)
            # Fall back to local context
    
    # Create context info
    now = time.time()
    context = ContextInfo(
        context_id=context_id,
        name=context_name,
        language=args.language,
        description=args.description or "",
        created_at=now,
        last_used=now,
        status="active"
    )
    
    # Register context
    context_registry[context_id] = context
    
    logger.info(f"Registered {args.language} context: {context_id} (name: {context_name})")
    
    # Return result
    result = {
        "context_id": context_id,
        "name": context_name,
        "language": args.language,
        "description": args.description or "",
        "created_at": datetime.utcfromtimestamp(now).isoformat() + "Z",
        "status": "active",
        "message": f"{args.language.capitalize()} context created successfully"
    }
    
    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


async def handle_stop_context(arguments: Any) -> Sequence[TextContent]:
    """Handle stop_context tool."""
    # Validate arguments
    args = StopContextSchema.model_validate(arguments)
    
    # Check if context exists
    if args.context_id not in context_registry:
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Context not found: {args.context_id}",
                    "code": "CONTEXT_NOT_FOUND"
                }, indent=2)
            )
        ]
    
    # Remove E2B context if exists
    if args.context_id in e2b_contexts:
        e2b_contexts.pop(args.context_id)
    
    # Remove from registry
    context = context_registry.pop(args.context_id)
    
    logger.info(f"Stopped context: {args.context_id} (name: {context.name})")
    
    # Return result
    result = {
        "context_id": args.context_id,
        "status": "stopped",
        "message": "Context stopped successfully"
    }
    
    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


async def handle_list_contexts(arguments: Any) -> Sequence[TextContent]:
    """Handle list_contexts tool."""
    # Build context list
    contexts = [
        {
            "context_id": ctx.context_id,
            "name": ctx.name,
            "language": ctx.language,
            "description": ctx.description,
            "status": ctx.status,
            "created_at": datetime.utcfromtimestamp(ctx.created_at).isoformat() + "Z",
            "last_used": datetime.utcfromtimestamp(ctx.last_used).isoformat() + "Z",
        }
        for ctx in context_registry.values()
    ]
    
    # Sort by created_at (newest first)
    contexts.sort(key=lambda x: x["created_at"], reverse=True)
    
    result = {
        "contexts": contexts,
        "total": len(contexts)
    }
    
    return [
        TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )
    ]


# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Code Interpreter MCP Server - Secure code execution via E2B',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Configuration Priority (highest to lowest):
  1. Command line arguments
  2. Environment variables
  3. .env file

Environment Variables:
  SANDBOX_URL   Code interpreter endpoint URL (e.g., http://localhost:5001)
  LOG_LEVEL     Log level (default: INFO)
        '''
    )
    
    parser.add_argument(
        '--sandbox-url',
        dest='sandbox_url',
        help='Code interpreter endpoint URL (e.g., http://localhost:5001)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=None,
        help='Log level'
    )
    
    parser.add_argument(
        '--disable-mock',
        action='store_true',
        help='Disable mock mode fallback, fail if E2B Sandbox is not available'
    )
    
    return parser.parse_args()


def get_config_value(args, arg_name, env_name, default=None):
    """Get configuration value with priority: CLI args > env vars > default."""
    # Priority 1: Command line argument
    arg_value = getattr(args, arg_name, None)
    if arg_value is not None:
        return arg_value
    
    # Priority 2: Environment variable
    env_value = os.getenv(env_name)
    if env_value is not None:
        return env_value
    
    # Priority 3: Default value
    return default


# ============================================================================
# Server Lifecycle
# ============================================================================

async def initialize_server(args=None):
    """Initialize server on startup."""
    global e2b_sandbox
    
    logger.info("="*60)
    logger.info("Code Interpreter MCP Server Starting...")
    logger.info("="*60)
    
    # Get configuration values
    sandbox_url = None
    disable_mock = False
    
    if args:
        sandbox_url = getattr(args, 'sandbox_url', None) or os.getenv("SANDBOX_URL")
        disable_mock = getattr(args, 'disable_mock', False) or os.getenv("DISABLE_MOCK", "").lower() in ("true", "1", "yes")
        
        # Update log level if specified
        log_level = get_config_value(args, 'log_level', 'LOG_LEVEL', 'INFO')
        if log_level:
            logger.setLevel(getattr(logging, log_level))
            logger.info(f"Log level set to: {log_level}")
    else:
        # Fallback to environment variables
        sandbox_url = os.getenv("SANDBOX_URL")
        disable_mock = os.getenv("DISABLE_MOCK", "").lower() in ("true", "1", "yes")
    
    if disable_mock:
        logger.info("Mock mode disabled - will fail if E2B Sandbox is not available")
    
    # Initialize E2B Sandbox if available
    if E2B_AVAILABLE:
        try:
            logger.info("Initializing E2B Sandbox...")
            
            # Create E2B Sandbox instance with sandbox_url
            if sandbox_url:
                e2b_sandbox = Sandbox(envd_url=sandbox_url)
                logger.info(f"Using code interpreter endpoint: {sandbox_url}")
            else:
                e2b_sandbox = Sandbox()  # Will use SANDBOX_URL from environment
                logger.info("Using SANDBOX_URL from environment")
            
            # Test connection (with fallback to continue even if health check fails)
            if e2b_sandbox.is_running():
                logger.info(f"✅ E2B Sandbox initialized successfully")
                logger.info(f"   Sandbox ID: {e2b_sandbox.sandbox_id}")
                logger.info(f"   Endpoint: {e2b_sandbox.envd_api_url}")
            else:
                if disable_mock:
                    logger.error("Code interpreter health check failed and mock mode is disabled")
                    raise RuntimeError("E2B Sandbox health check failed and mock mode is disabled")
                else:
                    logger.warning("Code interpreter health check failed, but continuing with E2B Sandbox")
                    logger.info(f"   Sandbox ID: {e2b_sandbox.sandbox_id}")
                    logger.info(f"   Endpoint: {e2b_sandbox.envd_api_url}")
                    # Don't set e2b_sandbox = None, continue with E2B mode
            
        except Exception as e:
            logger.error(f"Failed to initialize E2B Sandbox: {e}", exc_info=True)
            if disable_mock:
                logger.error("Mock mode is disabled, server will exit")
                raise
            else:
                logger.warning("Server will run in mock mode")
                e2b_sandbox = None
    else:
        if disable_mock:
            logger.error("E2B SDK not available and mock mode is disabled")
            raise RuntimeError("E2B SDK not available and mock mode is disabled")
        else:
            logger.warning("E2B SDK not available, running in mock mode")
    
    logger.info("Server initialization complete")
    logger.info(f"Supported languages: Python, JavaScript")
    logger.info(f"Available tools: 4 (run_code, create_context, stop_context, list_contexts)")
    logger.info(f"Mode: {'E2B Sandbox' if e2b_sandbox else 'Mock'}")
    logger.info("="*60)


async def cleanup_server():
    """Cleanup server on shutdown."""
    global e2b_sandbox
    
    logger.info("="*60)
    logger.info("Code Interpreter MCP Server Shutting Down...")
    logger.info("="*60)
    
    # Cleanup E2B Sandbox resources
    if e2b_sandbox:
        try:
            e2b_sandbox.kill()
            logger.info("E2B Sandbox terminated successfully")
        except Exception as e:
            logger.error(f"Error cleaning up E2B Sandbox: {e}")
    
    # Clear context registry
    context_registry.clear()
    e2b_contexts.clear()
    
    # Clear sandbox reference
    e2b_sandbox = None
    
    logger.info("Server cleanup complete")
    logger.info("="*60)


async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    
    # Parse command line arguments
    args = parse_args()
    
    # Initialize server with args
    await initialize_server(args)
    
    logger.info("Starting stdio server...")
    logger.info("Listening on stdin/stdout")
    
    try:
        # Run stdio server
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    finally:
        # Cleanup on shutdown
        await cleanup_server()
