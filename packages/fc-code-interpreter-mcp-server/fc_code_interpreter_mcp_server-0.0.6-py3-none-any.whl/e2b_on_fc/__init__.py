"""
E2B on Aliyun Function Compute SDK

This package provides a simplified SDK for code execution via code interpreter endpoints.
No Function Compute resource creation needed - just point to an existing endpoint.

Based on: https://github.com/aliyun-fc/e2b-on-aliyun-fc
"""

__version__ = "1.0.0"

# Use simplified Sandbox implementation
from e2b_on_fc.simple_sandbox import Sandbox
from e2b_on_fc.e2b_code_interpreter.models import Context, Execution

__all__ = [
    "Sandbox",
    "Context", 
    "Execution",
    "__version__",
]
