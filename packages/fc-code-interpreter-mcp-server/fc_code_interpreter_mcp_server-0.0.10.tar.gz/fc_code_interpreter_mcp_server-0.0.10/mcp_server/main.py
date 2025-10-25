#!/usr/bin/env python3
"""
FastMCP-based MCP Server for Sandbox Code Interpreter

This server uses FastMCP framework to provide a unified interface
supporting stdio, SSE, and HTTP Streamable transports.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

# FastMCP imports
from fastmcp import FastMCP
from fastmcp.server.http import create_sse_app
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# E2B imports
from e2b_on_fc import Sandbox as E2BSandbox
from e2b import TimeoutException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state
contexts: Dict[str, Dict[str, Any]] = {}
e2b_sandbox: Optional[E2BSandbox] = None
configured_sandbox_url: str = "http://localhost:5001"

# Initialize FastMCP server
mcp = FastMCP("Sandbox Code Interpreter")

async def initialize_e2b_sandbox(sandbox_url: str = 'http://localhost:5001'):
    """Initialize E2B sandbox connection."""
    global e2b_sandbox, configured_sandbox_url
    try:
        configured_sandbox_url = sandbox_url
        e2b_sandbox = E2BSandbox(envd_url=sandbox_url)
        logger.info(f"E2B sandbox initialized successfully with URL: {sandbox_url}")
    except Exception as e:
        logger.error(f"Failed to initialize E2B sandbox: {e}")
        raise

async def cleanup_e2b_sandbox():
    """Cleanup E2B sandbox connection."""
    global e2b_sandbox
    if e2b_sandbox:
        try:
            # E2B sandbox cleanup
            if hasattr(e2b_sandbox, 'close'):
                await e2b_sandbox.close()
            elif hasattr(e2b_sandbox, 'kill'):
                await e2b_sandbox.kill()
            logger.info("E2B sandbox closed successfully")
        except Exception as e:
            logger.error(f"Error closing E2B sandbox: {e}")
        finally:
            e2b_sandbox = None

@mcp.tool
async def run_code(code: str, context_id: Optional[str] = None, language: Optional[str] = None) -> str:
    """
    Execute code in the sandbox environment.
    
    Args:
        code: Code to execute
        context_id: Optional context ID for isolated execution
        language: Programming language (required if context_id is not provided)
        
    Returns:
        Execution result as string
    """
    try:
        # Validate parameters: if no context_id, language is required
        if not context_id and not language:
            return "Error: Either context_id or language parameter must be provided"
        
        if not e2b_sandbox:
            await initialize_e2b_sandbox()
        
        # Execute code using E2B sandbox with language parameter
        if language:
            execution = e2b_sandbox.run_code(code, language=language)
        else:
            execution = e2b_sandbox.run_code(code)
        
        # Format the result
        if execution.error:
            result = f"Error: {execution.error.name}: {execution.error.value}\n{execution.error.traceback}"
        else:
            # 收集所有输出
            output_parts = []
            
            # 添加 stdout 输出
            if execution.logs.stdout:
                stdout_lines = []
                for msg in execution.logs.stdout:
                    if hasattr(msg, 'line'):
                        stdout_lines.append(msg.line)
                    else:
                        stdout_lines.append(str(msg))
                stdout_output = "\n".join(stdout_lines)
                if stdout_output.strip():
                    output_parts.append(stdout_output)
            
            # 添加 stderr 输出
            if execution.logs.stderr:
                stderr_lines = []
                for msg in execution.logs.stderr:
                    if hasattr(msg, 'line'):
                        stderr_lines.append(msg.line)
                    else:
                        stderr_lines.append(str(msg))
                stderr_output = "\n".join(stderr_lines)
                if stderr_output.strip():
                    output_parts.append(f"stderr: {stderr_output}")
            
            # 添加执行结果
            if execution.text:
                output_parts.append(execution.text)
            
            # 组合所有输出
            if output_parts:
                result = "\n".join(output_parts)
            else:
                result = "Code executed successfully (no output)"
        
        # Update context if provided
        if context_id and context_id in contexts:
            contexts[context_id]["last_used"] = datetime.now().isoformat()
        
        return result
        
    except TimeoutException as e:
        error_msg = f"Code execution timeout: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool
async def create_context(language: str = "python", description: str = "") -> str:
    """
    Create a new execution context.
    
    Args:
        language: Programming language (default: python)
        description: Optional description for the context
        
    Returns:
        Context ID
    """
    try:
        import uuid
        context_id = str(uuid.uuid4())
        
        contexts[context_id] = {
            "id": context_id,
            "language": language,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat()
        }
        
        logger.info(f"Created context {context_id} with language {language}")
        return context_id
        
    except Exception as e:
        error_msg = f"Failed to create context: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool
async def stop_context(context_id: str) -> str:
    """
    Stop and remove a context.
    
    Args:
        context_id: Context ID to stop
        
    Returns:
        Success message
    """
    try:
        if context_id in contexts:
            del contexts[context_id]
            logger.info(f"Stopped context {context_id}")
            return f"Context {context_id} stopped successfully"
        else:
            return f"Context {context_id} not found"
            
    except Exception as e:
        error_msg = f"Failed to stop context: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool
async def list_contexts() -> str:
    """
    List all available contexts.
    
    Returns:
        JSON string of contexts
    """
    try:
        return json.dumps(list(contexts.values()), indent=2)
        
    except Exception as e:
        error_msg = f"Failed to list contexts: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool
async def health_check() -> str:
    """
    Check the health status of the configured sandbox service.
    
    Returns:
        Health status information
    """
    try:
        import aiohttp
        
        # Use the configured sandbox URL from server initialization
        sandbox_url = configured_sandbox_url
        
        # Ensure URL has /health endpoint
        if not sandbox_url.endswith('/health'):
            if not sandbox_url.endswith('/'):
                sandbox_url += '/'
            sandbox_url += 'health'
        
        logger.info(f"Checking health of sandbox service at: {sandbox_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(sandbox_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                status_code = response.status
                response_text = await response.text()
                
                if status_code == 200:
                    result = {
                        "status": "healthy",
                        "sandbox_url": sandbox_url,
                        "response_code": status_code,
                        "response_body": response_text.strip(),
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.info(f"Sandbox service is healthy: {sandbox_url}")
                else:
                    result = {
                        "status": "unhealthy",
                        "sandbox_url": sandbox_url,
                        "response_code": status_code,
                        "response_body": response_text.strip(),
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.warning(f"Sandbox service returned non-200 status: {status_code}")
                
                return json.dumps(result, indent=2)
                
    except aiohttp.ClientTimeout as e:
        error_msg = f"Health check timeout for {sandbox_url}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "timeout",
            "sandbox_url": sandbox_url,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
        
    except aiohttp.ClientError as e:
        error_msg = f"Health check connection error for {sandbox_url}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "connection_error",
            "sandbox_url": sandbox_url,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }, indent=2)
        
    except Exception as e:
        error_msg = f"Health check failed for {sandbox_url}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "sandbox_url": sandbox_url,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }, indent=2)

async def initialize_server(sandbox_url: str):
    """Initialize server resources."""
    try:
        await initialize_e2b_sandbox(sandbox_url)
        logger.info("Server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

async def cleanup_server():
    """Cleanup server resources."""
    try:
        await cleanup_e2b_sandbox()
        logger.info("Server cleanup completed")
    except Exception as e:
        logger.error(f"Error during server cleanup: {e}")

def parse_args():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FastMCP Sandbox Code Interpreter Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "http"], default="stdio",
                       help="Transport protocol to use")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to")
    parser.add_argument("--path", default="/mcp", help="Path for HTTP transport")
    parser.add_argument("--sandbox-url", default="http://localhost:5001", 
                       help="E2B sandbox URL (default: http://localhost:5001)")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_args()
        
        # Get host and port from args or environment
        host = args.host or os.getenv('MCP_HOST', '0.0.0.0')
        port = args.port or int(os.getenv('MCP_PORT', '3000'))
        path = args.path or os.getenv('MCP_PATH', '/mcp')
        
        logger.info(f"Starting FastMCP server with {args.transport} transport")
        logger.info(f"Host: {host}, Port: {port}")
        logger.info(f"Sandbox URL: {args.sandbox_url}")
        
        # Initialize server with sandbox URL
        asyncio.run(initialize_server(args.sandbox_url))
        
        if args.transport == "stdio":
            logger.info("Using stdio transport")
            # FastMCP stdio transport
            mcp.run(transport="stdio")
            
        elif args.transport == "sse":
            logger.info(f"Using SSE transport on http://{host}:{port}{path}")
            # Create SSE app with CORS support
            # Try different path configurations to fix 404/307 errors
            sse_app = create_sse_app(
                server=mcp,
                message_path=f"{path}/message",
                sse_path=path,
                middleware=[
                    Middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_credentials=True,
                        allow_methods=["GET", "POST", "OPTIONS"],
                        allow_headers=["*"],
                    )
                ]
            )
            # Run the SSE app
            import uvicorn
            uvicorn.run(sse_app, host=host, port=port)
            
        elif args.transport == "http":
            logger.info(f"Using HTTP transport on http://{host}:{port}{path}")
            # FastMCP HTTP transport with CORS support
            # Create streamable HTTP app with CORS middleware
            from fastmcp.server.http import create_streamable_http_app
            http_app = create_streamable_http_app(
                server=mcp,
                streamable_http_path=path,
                middleware=[
                    Middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_credentials=True,
                        allow_methods=["GET", "POST", "OPTIONS"],
                        allow_headers=["*"],
                    )
                ]
            )
            # Run the HTTP app
            import uvicorn
            uvicorn.run(http_app, host=host, port=port)
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
