#!/usr/bin/env python3
"""Test E2B SDK run_code with local code interpreter at http://localhost:5001"""

import sys
import os
from pathlib import Path

# Set environment variable to point to local endpoint
os.environ['SANDBOX_URL'] = 'http://localhost:5001'

try:
    from e2b_on_fc import Sandbox
    
    print("=" * 60)
    print("Testing E2B SDK with local Code Interpreter")
    print("Endpoint: http://localhost:5001")
    print("=" * 60)
    
    # Create sandbox with explicit URL
    print(f"\n[1] Creating sandbox with local endpoint")
    try:
        sandbox = Sandbox(envd_url="http://localhost:5001")
        print(f"✅ Sandbox created: {sandbox.sandbox_id}")
        print(f"✅ Sandbox API URL: {sandbox.envd_api_url}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nPlease ensure the code interpreter service is running at http://localhost:5001")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Test 1: Simple Python code execution
    print("\n[2] Test: Simple Python print")
    try:
        execution = sandbox.run_code("print('Hello from E2B!')")
        print(f"✅ Execution completed")
        print(f"   Logs: {execution.logs}")
        if execution.error:
            print(f"   Error: {execution.error}")
        if execution.results:
            print(f"   Results: {execution.results}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Python code with variables
    print("\n[3] Test: Python variables and calculation")
    try:
        execution = sandbox.run_code("""
x = 10
y = 20
result = x + y
print(f"Result: {result}")
""")
        print(f"✅ Execution completed")
        print(f"   Logs: {execution.logs}")
        if execution.results:
            print(f"   Results: {execution.results}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
    
    # Test 3: Python code with imports
    print("\n[4] Test: Python imports and math")
    try:
        execution = sandbox.run_code("""
import math
result = math.sqrt(16)
print(f"Square root of 16 is: {result}")
""")
        print(f"✅ Execution completed")
        print(f"   Logs: {execution.logs}")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
    
    # Test 4: JavaScript code (if supported)
    print("\n[5] Test: JavaScript code")
    try:
        execution = sandbox.run_code(
            "console.log('Hello from JavaScript!');",
            language="javascript"
        )
        print(f"✅ Execution completed")
        print(f"   Logs: {execution.logs}")
    except Exception as e:
        print(f"⚠️  JavaScript execution failed (may not be supported): {e}")
    
    # Test 5: Context-based execution
    print("\n[6] Test: Context-based execution")
    try:
        context = sandbox.create_code_context()
        print(f"✅ Created context: {context.id}")
        
        # Execute code in context
        execution1 = sandbox.run_code("x = 100", context=context)
        print(f"✅ Set variable x in context")
        
        execution2 = sandbox.run_code("print(f'x = {x}')", context=context)
        print(f"✅ Read variable x from context")
        print(f"   Logs: {execution2.logs}")
    except Exception as e:
        print(f"⚠️  Context execution failed: {e}")
    
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Failed to import E2B SDK: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
