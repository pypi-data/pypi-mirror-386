"""
Simplified Sandbox implementation that directly uses envd_url
without creating Function Compute resources.
"""

import os
import logging
import httpx
from typing import Optional, Dict, Union, Literal
from uuid import uuid4
import random

from e2b_on_fc.e2b_code_interpreter.models import (
    Execution,
    Context,
    ExecutionError,
    Result,
    Logs,
    extract_exception,
    parse_output,
    OutputHandler,
    OutputMessage,
)
from e2b_on_fc.e2b_code_interpreter.constants import DEFAULT_TIMEOUT
from e2b_on_fc.e2b_code_interpreter.exceptions import (
    format_execution_timeout_error,
    format_request_timeout_error,
)

logger = logging.getLogger(__name__)


def generate_session_id() -> str:
    """
    Generate a UUID v4 that starts with 'a'.
    
    :return: A valid UUID v4 string starting with 'a'
    """
    while True:
        # Generate a random UUID v4
        session_id = str(uuid4())
        # Check if it starts with 'a'
        if session_id.startswith('a'):
            return session_id
        # If not, modify the first character to 'a' while keeping it valid
        # Replace the first character with 'a' - UUID4 version and variant bits are already correct
        session_id = 'a' + session_id[1:]
        return session_id


class Sandbox:
    """
    Simplified Sandbox that connects directly to a code interpreter endpoint.
    
    Usage:
        # Use environment variable
        sandbox = Sandbox()
        
        # Or specify URL directly
        sandbox = Sandbox(envd_url="http://localhost:5001")
    """
    
    def __init__(
        self,
        envd_url: Optional[str] = None,
        request_timeout: Optional[float] = 60.0,
        session_id: Optional[str] = None,
    ):
        """
        Create a sandbox client.
        
        :param envd_url: Code interpreter endpoint URL. If not provided, reads from 
                        SANDBOX_URL (preferred) or ENVD_URL/LOCAL_ENDPOINT environment variables
        :param request_timeout: Request timeout in seconds (default: 60s)
        :param session_id: Session ID to use. If not provided, generates a new one
        """
        # Get envd_url from parameter or environment
        self._envd_url = envd_url or os.getenv("SANDBOX_URL") or os.getenv("ENVD_URL") or os.getenv("LOCAL_ENDPOINT")
        
        if not self._envd_url:
            raise ValueError(
                "envd_url must be provided or set via ENVD_URL/LOCAL_ENDPOINT environment variable"
            )
        
        # Ensure URL doesn't end with slash
        self._envd_url = self._envd_url.rstrip('/')
        
        self._request_timeout = request_timeout
        
        # Use provided session ID or generate a new one
        self._session_id = session_id or generate_session_id()
        
        # Create HTTP client with custom headers
        self._client = httpx.Client(
            base_url=self._envd_url,
            timeout=httpx.Timeout(request_timeout),
            headers={
                "X-CI-SESSION-ID": self._session_id,
                "Content-Type": "application/json",
                "User-Agent": "e2b-on-fc-sdk/1.0.0"
            }
        )
        
        # Generate a pseudo sandbox_id for compatibility
        self._sandbox_id = f"sandbox-{uuid4().hex[:8]}"
        
        logger.info(f"Sandbox client initialized with endpoint: {self._envd_url}")
    
    @property
    def envd_api_url(self) -> str:
        """Return the code interpreter endpoint URL."""
        return self._envd_url
    
    @property
    def sandbox_id(self) -> str:
        """Return a pseudo sandbox ID."""
        return self._sandbox_id
    
    @property
    def session_id(self) -> str:
        """Return the session ID used in X-CI-SESSION-ID header."""
        return self._session_id
    
    def run_code(
        self,
        code: str,
        language: Optional[str] = None,
        context: Optional[Context] = None,
        on_stdout: Optional[OutputHandler[OutputMessage]] = None,
        on_stderr: Optional[OutputHandler[OutputMessage]] = None,
        on_result: Optional[OutputHandler[Result]] = None,
        on_error: Optional[OutputHandler[ExecutionError]] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        request_timeout: Optional[float] = None,
    ) -> Execution:
        """
        Execute code in the code interpreter.
        
        :param code: Code to execute
        :param language: Language to use (default: python)
        :param context: Execution context for stateful execution
        :param on_stdout: Callback for stdout messages
        :param on_stderr: Callback for stderr messages
        :param on_result: Callback for results
        :param on_error: Callback for errors
        :param envs: Environment variables
        :param timeout: Code execution timeout in seconds
        :param request_timeout: HTTP request timeout in seconds
        :return: Execution result
        """
        logger.debug(f"Executing {language or 'python'} code: {code[:100]}...")
        
        timeout = None if timeout == 0 else (timeout or DEFAULT_TIMEOUT)
        request_timeout = request_timeout or self._request_timeout
        context_id = context.id if context else None
        
        try:
            with self._client.stream(
                "POST",
                "/execute",
                json={
                    "code": code,
                    "context_id": context_id,
                    "language": language,
                    "env_vars": envs,
                },
                timeout=httpx.Timeout(request_timeout),
            ) as response:
                response.raise_for_status()
                
                execution = Execution(logs=Logs(stdout=[], stderr=[]), results=[], error=None)
                
                # Process streaming response
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    # parse_output takes execution and line as parameters
                    parse_output(
                        execution,
                        line,
                        on_stdout=on_stdout,
                        on_stderr=on_stderr,
                        on_result=on_result,
                        on_error=on_error,
                    )
                
                return execution
        
        except httpx.TimeoutException as e:
            if "execute" in str(e):
                raise format_execution_timeout_error(timeout)
            raise format_request_timeout_error()
        
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"Code execution failed: {error_msg}")
            raise Exception(error_msg)
        
        except Exception as e:
            logger.error(f"Code execution failed: {e}", exc_info=True)
            raise
    
    def create_code_context(self, language: Optional[str] = None) -> Context:
        """
        Create a new execution context.
        
        :param language: Language of the context. If not specified, defaults to Python
        :return: Context object
        """
        try:
            # Prepare request data
            data = {}
            if language:
                data["language"] = language
            
            response = self._client.post(
                "/contexts",
                json=data,
                timeout=httpx.Timeout(self._request_timeout),
            )
            response.raise_for_status()
            
            response_data = response.json()
            context_id = response_data.get("id") or response_data.get("context_id")
            context_language = response_data.get("language", language or "python")
            cwd = response_data.get("cwd", "/")
            
            logger.debug(f"Created {context_language} context: {context_id}")
            return Context(
                context_id=context_id,
                language=context_language,
                cwd=cwd,
            )
        
        except Exception as e:
            logger.error(f"Failed to create context: {e}", exc_info=True)
            raise
    
    def is_running(self) -> bool:
        """
        Check if the code interpreter is running.
        
        :return: True if running, False otherwise
        """
        try:
            response = self._client.get(
                "/health",
                timeout=httpx.Timeout(5.0),
                headers={
                    "X-CI-SESSION-ID": self._session_id,
                    "Content-Type": "application/json",
                }
            )
            return response.status_code == 200
        except:
            return False
    
    def kill(self):
        """
        Close the HTTP client.
        """
        self._client.close()
        logger.info("Sandbox client closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()
    
    def __del__(self):
        try:
            self.kill()
        except:
            pass
