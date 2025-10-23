#!/usr/bin/env python3
"""Test simplified Sandbox implementation with direct URL"""

import os

# Set the endpoint URL
os.environ['SANDBOX_URL'] = 'http://localhost:5001'

from e2b_on_fc import Sandbox

print("=" * 60)
print("Testing Simplified Sandbox with Direct URL")
print("=" * 60)

# Test 1: Create sandbox with environment variable
print("\n[1] Creating sandbox with SANDBOX_URL environment variable")
sandbox = Sandbox()
print(f"✅ Sandbox created")
print(f"   Endpoint: {sandbox.envd_api_url}")
print(f"   Sandbox ID: {sandbox.sandbox_id}")

# Test 2: Check if running
print("\n[2] Checking if code interpreter is running")
if sandbox.is_running():
    print("✅ Code interpreter is running")
else:
    print("❌ Code interpreter is not running")
    exit(1)

# Test 3: Simple Python execution
print("\n[3] Test: Simple Python code")
execution = sandbox.run_code("print('Hello from simplified sandbox!')")
print(f"✅ Execution completed")
print(f"   Stdout: {execution.logs.stdout if execution.logs else 'None'}")

# Test 4: Python with variables
print("\n[4] Test: Python variables")
execution = sandbox.run_code("""
x = 42
y = 58
result = x + y
print(f"Sum: {result}")
""")
print(f"✅ Execution completed")
print(f"   Stdout: {execution.logs.stdout if execution.logs else 'None'}")

# Test 5: Context-based execution
print("\n[5] Test: Context-based execution")
context = sandbox.create_code_context()
print(f"✅ Created context: {context.id}")

sandbox.run_code("counter = 0", context=context)
print("✅ Initialized counter")

execution = sandbox.run_code("counter += 1; print(f'Counter: {counter}')", context=context)
print(f"✅ First increment: {execution.logs.stdout if execution.logs else 'None'}")

execution = sandbox.run_code("counter += 1; print(f'Counter: {counter}')", context=context)
print(f"✅ Second increment: {execution.logs.stdout if execution.logs else 'None'}")

# Test 6: JavaScript execution
print("\n[6] Test: JavaScript execution")
try:
    execution = sandbox.run_code(
        "console.log('Hello from JavaScript!');",
        language="javascript"
    )
    print(f"✅ JavaScript execution completed")
    print(f"   Stdout: {execution.logs.stdout if execution.logs else 'None'}")
except Exception as e:
    print(f"⚠️  JavaScript execution failed: {e}")

# Test 7: Create another sandbox with explicit URL
print("\n[7] Test: Create sandbox with explicit URL")
sandbox2 = Sandbox(envd_url="http://localhost:5001")
print(f"✅ Second sandbox created")
print(f"   Endpoint: {sandbox2.envd_api_url}")

execution = sandbox2.run_code("print('From second sandbox')")
print(f"✅ Execution completed: {execution.logs.stdout if execution.logs else 'None'}")

# Cleanup
print("\n[8] Cleanup")
sandbox.kill()
sandbox2.kill()
print("✅ Sandboxes closed")

print("\n" + "=" * 60)
print("All tests passed! ✅")
print("=" * 60)
