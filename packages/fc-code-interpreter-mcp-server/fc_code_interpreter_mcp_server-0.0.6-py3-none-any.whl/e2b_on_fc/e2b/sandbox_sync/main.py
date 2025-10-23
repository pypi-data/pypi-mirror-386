import logging
from alibabacloud_credentials.client import ac
import httpx

from typing import Dict, Optional, overload

from e2b.api.client.types import Unset
from e2b.connection_config import ConnectionConfig, ProxyTypes
from e2b.envd.api import ENVD_API_HEALTH_ROUTE, handle_envd_api_exception
from e2b.exceptions import SandboxException, format_request_timeout_error
from e2b.sandbox.main import SandboxSetup
from e2b.sandbox.utils import class_method_variant
from e2b.sandbox_sync.filesystem.filesystem import Filesystem
from e2b.sandbox_sync.commands.command import Commands
from e2b.sandbox_sync.commands.pty import Pty
from e2b.sandbox_sync.sandbox_api import SandboxApi, SandboxInfo
from e2b.sandbox_backend.fc_backend import FCBackend
import time
import os

logger = logging.getLogger(__name__)

class TransportWithLogger(httpx.HTTPTransport):
    def handle_request(self, request):
        url = f"{request.url.scheme}://{request.url.host}{request.url.path}"
        logger.info(f"Request: {request.method} {url}")
        response = super().handle_request(request)

        # data = connect.GzipCompressor.decompress(response.read()).decode()
        logger.info(f"Response: {response.status_code} {url}")

        return response


class Sandbox(SandboxSetup, SandboxApi):
    """
    E2B cloud sandbox is a secure and isolated cloud environment.

    The sandbox allows you to:
    - Access Linux OS
    - Create, list, and delete files and directories
    - Run commands
    - Run isolated code
    - Access the internet

    Check docs [here](https://e2b.dev/docs).

    Use the `Sandbox()` to create a new sandbox.

    Example:
    ```python
    from e2b import Sandbox

    sandbox = Sandbox()
    ```
    """

    @property
    def files(self) -> Filesystem:
        """
        Module for interacting with the sandbox filesystem.
        """
        return self._filesystem

    @property
    def commands(self) -> Commands:
        """
        Module for running commands in the sandbox.
        """
        return self._commands

    @property
    def pty(self) -> Pty:
        """
        Module for interacting with the sandbox pseudo-terminal.
        """
        return self._pty

    @property
    def sandbox_id(self) -> str:
        """
        Unique identifier of the sandbox
        """
        return self._sandbox_id

    @property
    def envd_api_url(self) -> str:
        return self._envd_api_url

    @property
    def _envd_access_token(self) -> str:
        """Private property to access the envd token"""
        return self.__envd_access_token

    @_envd_access_token.setter
    def _envd_access_token(self, value: Optional[str]):
        """Private setter for envd token"""
        self.__envd_access_token = value

    @property
    def connection_config(self) -> ConnectionConfig:
        return self._connection_config
    
    @property
    def function_name(self) -> str:
        return self._function_name

    @property
    def trigger_name(self) -> str:
        return self._trigger_name

    def __init__(
        self,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        sandbox_id: Optional[str] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
        image: Optional[str] = None,
        endpoint: Optional[str] = None,
        log_store: Optional[str] = None,
        log_project: Optional[str] = None,
        security_group_id: Optional[str] = None,
        v_switch_id: Optional[str] = None,
        vpc_id: Optional[str] = None,
        cpu: Optional[float] = 0.35,
        memory: Optional[int] = 512,
    ):
        """
        Create a new sandbox.

        By default, the sandbox is created from the default `base` sandbox template.

        :param template: Sandbox template name or ID
        :param timeout: Timeout for the sandbox in **seconds**, default to 300 seconds. Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users
        :param metadata: Custom metadata for the sandbox
        :param envs: Custom environment variables for the sandbox
        :param api_key: E2B API Key to use for authentication, defaults to `E2B_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**

        :return: sandbox instance for the new sandbox
        """
        super().__init__()

        if sandbox_id and (metadata is not None or template is not None):
            raise SandboxException(
                "Cannot set metadata or timeout when connecting to an existing sandbox. "
                "Use Sandbox.connect method instead.",
            )

        connection_headers = {}
        
        self.client = FCBackend(endpoint)
        self._trigger_name = None
        self._function_name = None
        self._envd_api_url = None
        if debug:
            self._sandbox_id = "debug_sandbox_id"
            self._envd_version = "v1.0"
            self._envd_access_token = None
            # For local testing, use LOCAL_ENDPOINT env var or default to localhost:5001
            local_endpoint = os.getenv("LOCAL_ENDPOINT", "http://localhost:5001")
            self._envd_api_url = local_endpoint
        elif sandbox_id is not None:
            self._function_name = sandbox_id
            self._sandbox_id = sandbox_id
            response = self.client._list_triggers(self._function_name)
            isTriggerCreated = False
            for trigger in response.body.triggers:
                if trigger.trigger_type == "http":
                    isTriggerCreated = True
                    self._trigger_name = trigger.trigger_name
                    self._envd_api_url = trigger.http_trigger.url_internet
                    logger.info(self._envd_api_url)
            if not isTriggerCreated:
                logger.warning("fucntion name: %s, trigger is not created", self._function_name) 
                return 
            
            response = self.client._get_concurrency_config(self._function_name)
            if response.body.reserved_concurrency != 1:
                logger.warning("fucntion name: %s, concurrency config is wrong", self._function_name) 
                return 

            response = self.client._get_provision_config(self._function_name)
            if response.body.target != 1:
                logger.warning("fucntion name: %s, provision config is wrong", self._function_name) 
                return 

            if response.body.current != 1:
                response = self.client._list_instances(self._function_name)
                if len(response.body.instances) != 1:
                    logger.warning("fucntion name: %s, instance is not ready", self._function_name) 
                    return 

            # response = SandboxApi.get_info(sandbox_id)

            # self._sandbox_id = sandbox_id
            # self._envd_version = response.envd_version
            # self._envd_access_token = response._envd_access_token

            # if response._envd_access_token is not None and not isinstance(
            #         response._envd_access_token, Unset
            # ):
            #     connection_headers["X-Access-Token"] = response._envd_access_token
        else:
            # template = template or self.default_template
            # timeout = timeout or self.default_sandbox_timeout
            # response = SandboxApi._create_sandbox(
            #     template=template,
            #     api_key=api_key,
            #     timeout=timeout,
            #     metadata=metadata,
            #     env_vars=envs,
            #     domain=domain,
            #     debug=debug,
            #     request_timeout=request_timeout,
            #     secure=secure or False,
            #     proxy=proxy,
            # )
            # self._sandbox_id = response.sandbox_id
            # self._envd_version = response.envd_version

            # if response.envd_access_token is not None and not isinstance(
            #     response.envd_access_token, Unset
            # ):
            #     self._envd_access_token = response.envd_access_token
            #     connection_headers["X-Access-Token"] = response.envd_access_token
            # else:
            #     self._envd_access_token = None

            
            response = self.client._create_function(image,log_store,log_project,security_group_id,v_switch_id,vpc_id,cpu,memory)
            self._function_name = response.body.function_name
            logger.info(self._function_name)
            logger.info("create function success")

            response = self.client._create_trigger(self._function_name)
            self._trigger_name = response.body.trigger_name
            self._envd_api_url = response.body.http_trigger.url_internet
            logger.info(response.body.http_trigger.url_internet)
            logger.info("create trigger success")

            self.client._put_provision_config(self._function_name)
            logger.info("put provision config success")
            self.client._put_concurrency_config(self._function_name)
            logger.info("put concurrency config success")

            retry_count = 0
            max_retries = 300
            while True:
                response = self.client._list_instances(self._function_name)
                instanceLen = len(response.body.instances)
                logger.info("current instance: ", instanceLen)
                if instanceLen >= 1:
                    break

                if retry_count >= max_retries:
                    raise TimeoutError("Reached maximum retry limit of 300s for checking provision config.")
                time.sleep(1)
                retry_count += 1
            logger.info(retry_count)
            
        self._sandbox_id = self._function_name
        self._envd_version = "v1.0"
        self._transport = TransportWithLogger(limits=self._limits, proxy=proxy)
        self._connection_config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=connection_headers,
            proxy=proxy,
        )

        self._envd_api = httpx.Client(
            base_url=self.envd_api_url,
            transport=self._transport,
            headers=self.connection_config.headers,
        )

        self._filesystem = Filesystem(
            self.envd_api_url,
            self._envd_version,
            self.connection_config,
            self._transport._pool,
            self._envd_api,
        )
        self._commands = Commands(
            self.envd_api_url,
            self.connection_config,
            self._transport._pool,
        )
        self._pty = Pty(
            self.envd_api_url,
            self.connection_config,
            self._transport._pool,
        )

    def is_running(self, request_timeout: Optional[float] = None) -> bool:
        """
        Check if the sandbox is running.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox is running, `False` otherwise

        Example
        ```python
        sandbox = Sandbox()
        sandbox.is_running() # Returns True

        sandbox.kill()
        sandbox.is_running() # Returns False
        ```
        """
        try:
            r = self._envd_api.get(
                ENVD_API_HEALTH_ROUTE,
                timeout=self.connection_config.get_request_timeout(request_timeout),
            )

            if r.status_code == 502:
                return False

            err = handle_envd_api_exception(r)

            if err:
                raise err

        except httpx.TimeoutException:
            raise format_request_timeout_error()

        return True

    @classmethod
    def connect(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        proxy: Optional[ProxyTypes] = None,
        endpoint: Optional[str] = None,
    ):
        """
        Connects to an existing Sandbox.
        With sandbox ID you can connect to the same sandbox from different places or environments (serverless functions, etc).

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication, defaults to `E2B_API_KEY` environment variable
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**

        :return: sandbox instance for the existing sandbox

        @example
        ```python
        sandbox = Sandbox()
        sandbox_id = sandbox.sandbox_id

        # Another code block
        same_sandbox = Sandbox.connect(sandbox_id)
        ```
        """
        if endpoint is None:
            endpoint = os.getenv("ENDPOINT")
        return cls(
            sandbox_id=sandbox_id,
            api_key=api_key,
            domain=domain,
            debug=debug,
            proxy=proxy,
            endpoint=endpoint,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()

    @overload
    def kill(self, request_timeout: Optional[float] = None) -> bool:
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        ...

    @overload
    @staticmethod
    def kill(
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> bool:
        """
        Kill the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication, defaults to `E2B_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request

        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        ...

    @class_method_variant("_cls_kill")
    def kill(self, request_timeout: Optional[float] = None) -> bool:  # type: ignore
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request
        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        # config_dict = self.connection_config.__dict__
        # config_dict.pop("access_token", None)
        # config_dict.pop("api_url", None)

        # if request_timeout:
        #     config_dict["request_timeout"] = request_timeout

        # SandboxApi._cls_kill(
        #     sandbox_id=self.sandbox_id,
        #     **config_dict,
        # )

        if self._trigger_name is not None:
            self.client._delete_trigger(self._function_name, self._trigger_name)
            logger.info("delete trigger success")

        self.client._delete_provision_config(self._function_name)
        response = self.client._list_concurrency_config(self._function_name)
        if len(response.body.configs) > 0:
            self.client._delete_concurrency_config(self._function_name)
            logger.info("delete concurrency config success")

        retry_count = 0
        max_retries = 120
        while True:
            response = self.client._get_provision_config(self._function_name)
            if response is None or (response.body.current == 0 and response.body.target == 0 and response.body.current_error == "" and response.body.always_allocate_cpu == False and response.body.always_allocate_gpu == False):
                break

            logger.info("waiting for provision config to be deleted")     
            if retry_count >= max_retries:
                raise TimeoutError("Reached maximum retry limit of 120s for checking provision config.")
            time.sleep(1)
            retry_count += 1
        logger.info("delete provision config success")

        self.client._delete_function(self._function_name)
        logger.info("delete function success")
    
    @classmethod
    def _cls_kill(
        cls,
        sandbox_id: str,
        endpoint: Optional[str] = None,
    ) -> SandboxInfo:
        if endpoint is None:
            endpoint = os.getenv("ENDPOINT")
        client = FCBackend(endpoint)

        trigger_name = None
        function_name = sandbox_id
        response = client._list_triggers(sandbox_id)
        for trigger in response.body.triggers:
            if trigger.trigger_type == "http":
                trigger_name = trigger.trigger_name

        if trigger_name is not None:
            client._delete_trigger(function_name, trigger_name)
            logger.info("delete trigger success")

        client._delete_provision_config(function_name)
        response = client._list_concurrency_config(function_name)
        if len(response.body.configs) > 0:
            client._delete_concurrency_config(function_name)
            logger.info("delete concurrency config success")

        max_retries = 120
        retry_count = 0
        while True:
            response = client._get_provision_config(function_name)
            if response is None or (response.body.current == 0 and response.body.target == 0 and response.body.current_error == "" and response.body.always_allocate_cpu == False and response.body.always_allocate_gpu == False):
                break

            logger.info("waiting for provision config to be deleted")     
            if retry_count >= max_retries:
                raise TimeoutError("Reached maximum retry limit of 120 for checking provision config.")
            time.sleep(1)
            retry_count += 1
        logger.info("delete provision config success")

        client._delete_function(sandbox_id)
        logger.info("delete function success")

    @overload
    def set_timeout(
        self,
        timeout: int,
        request_timeout: Optional[float] = None,
    ) -> None:
        """
        Set the timeout of the sandbox.
        After the timeout expires the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param timeout: Timeout for the sandbox in **seconds**
        :param request_timeout: Timeout for the request in **seconds**
        """
        ...

    @overload
    @staticmethod
    def set_timeout(
        sandbox_id: str,
        timeout: int,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> None:
        """
        Set the timeout of the sandbox specified by sandbox ID.
        After the timeout expires the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param sandbox_id: Sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**
        :param api_key: E2B API Key to use for authentication, defaults to `E2B_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request
        """
        ...

    @class_method_variant("_cls_set_timeout")
    def set_timeout(  # type: ignore
        self,
        timeout: int,
        request_timeout: Optional[float] = None,
    ) -> None:
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        SandboxApi._cls_set_timeout(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **config_dict,
        )

    @classmethod
    def list(
        cls,
        endpoint: Optional[str] = None,
    ) -> SandboxInfo:
        if endpoint is None:
            endpoint = os.getenv("ENDPOINT")
        client = FCBackend(endpoint)
        return client.list()