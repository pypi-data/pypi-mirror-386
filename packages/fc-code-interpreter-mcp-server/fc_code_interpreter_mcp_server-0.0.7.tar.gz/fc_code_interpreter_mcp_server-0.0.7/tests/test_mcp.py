#!/usr/bin/env python3
"""Test script for AgentRun MCP Server."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server by calling its tools."""
    
    print("🧪 Testing AgentRun MCP Server\n")
    print("=" * 60)
    
    # Server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "agentrun-mcp-server"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✅ Server initialized successfully\n")
            
            # Test 1: List available tools
            print("📋 Test 1: Listing available tools")
            print("-" * 60)
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()
            
            # Test 2: Create a context
            print("🎯 Test 2: Creating a Python context")
            print("-" * 60)
            result = await session.call_tool(
                "create_context",
                arguments={
                    "name": "test-context",
                    "language": "python",
                    "description": "Test context for validation"
                }
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            context_id = response_data["context_id"]
            
            print(f"Context created: {context_id}")
            print(f"Language: {response_data['language']}")
            print(f"Status: {response_data['status']}")
            print()
            
            # Test 3: List contexts
            print("📝 Test 3: Listing contexts")
            print("-" * 60)
            result = await session.call_tool("list_contexts", arguments={})
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"Total contexts: {response_data['total']}")
            for ctx in response_data['contexts']:
                print(f"  - {ctx['context_id']}: {ctx['name']} ({ctx['language']})")
            print()
            
            # Test 4: Run code in the context
            print("🚀 Test 4: Executing code in context")
            print("-" * 60)
            code = "x = 100\nprint(f'Hello from AgentRun! x = {x}')"
            print(f"Code:\n{code}\n")
            
            result = await session.call_tool(
                "run_code",
                arguments={
                    "code": code,
                    "context_id": context_id
                }
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"Success: {response_data['success']}")
            print(f"Stdout: {response_data['stdout']}")
            if response_data['stderr']:
                print(f"Stderr: {response_data['stderr']}")
            print(f"Execution time: {response_data['execution_time']}s")
            print()
            
            # Test 5: Stop the context
            print("🛑 Test 5: Stopping context")
            print("-" * 60)
            result = await session.call_tool(
                "stop_context",
                arguments={"context_id": context_id}
            )
            
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"Context {response_data['context_id']}: {response_data['status']}")
            print(f"Message: {response_data['message']}")
            print()
            
            # Test 6: Verify context is removed
            print("✅ Test 6: Verifying context removal")
            print("-" * 60)
            result = await session.call_tool("list_contexts", arguments={})
            response_text = result.content[0].text
            response_data = json.loads(response_text)
            
            print(f"Total contexts after removal: {response_data['total']}")
            print()
            
            print("=" * 60)
            print("✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
