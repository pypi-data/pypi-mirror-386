#!/usr/bin/env python3
"""Test MCP Server with E2B SDK integration"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set SANDBOX_URL for testing
os.environ['SANDBOX_URL'] = 'http://localhost:5001'

import asyncio
import mcp_server.server as server_module
from mcp_server.server import initialize_server, cleanup_server, context_registry, e2b_contexts

async def test_server():
    print("=" * 60)
    print("Testing MCP Server with E2B SDK")
    print("=" * 60)
    
    # Test 1: Initialize server
    print("\n[1] Initializing server...")
    try:
        await initialize_server()
        print("✅ Server initialized successfully")
        
        # Get the sandbox from the module after initialization
        e2b_sandbox = server_module.e2b_sandbox
        
        if e2b_sandbox:
            print(f"   Sandbox endpoint: {e2b_sandbox.envd_api_url}")
            print(f"   Sandbox ID: {e2b_sandbox.sandbox_id}")
        else:
            print("⚠️  No sandbox available")
            return
    except Exception as e:
        print(f"❌ Failed to initialize server: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Create context
    print("\n[2] Creating execution context...")
    try:
        # Get sandbox reference again
        e2b_sandbox = server_module.e2b_sandbox
        
        # Manually create context via E2B SDK
        e2b_context = e2b_sandbox.create_code_context()
        context_id = f"ctx-{e2b_context.id}"
        
        # Register in server
        from mcp_server.server import ContextInfo
        context_info = ContextInfo(
            context_id=context_id,
            name="test-context",
            language="python",
            description="Test context",
            created_at=asyncio.get_event_loop().time(),
            last_used=asyncio.get_event_loop().time(),
        )
        context_registry[context_id] = context_info
        e2b_contexts[context_id] = e2b_context
        
        print(f"✅ Context created: {context_id}")
    except Exception as e:
        print(f"❌ Failed to create context: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Execute code
    print("\n[3] Executing Python code...")
    try:
        execution = e2b_sandbox.run_code(
            "print('Hello from MCP Server test!')",
            context=e2b_context
        )
        print(f"✅ Code executed successfully")
        if execution.logs:
            print(f"   Stdout: {execution.logs.stdout}")
    except Exception as e:
        print(f"❌ Failed to execute code: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Execute with variables
    print("\n[4] Executing code with variables...")
    try:
        e2b_sandbox.run_code("counter = 0", context=e2b_context)
        execution = e2b_sandbox.run_code("counter += 1; print(f'Counter: {counter}')", context=e2b_context)
        print(f"✅ Code executed successfully")
        if execution.logs:
            print(f"   Stdout: {execution.logs.stdout}")
    except Exception as e:
        print(f"❌ Failed to execute code: {e}")
    
    # Test 5: List contexts
    print("\n[5] Listing active contexts...")
    print(f"   Active contexts: {len(context_registry)}")
    for ctx_id, ctx_info in context_registry.items():
        print(f"   - {ctx_id}: {ctx_info.name} ({ctx_info.language})")
    
    # Cleanup
    print("\n[6] Cleaning up...")
    try:
        await cleanup_server()
        print("✅ Server cleaned up successfully")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "=" * 60)
    print("MCP Server test completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_server())
