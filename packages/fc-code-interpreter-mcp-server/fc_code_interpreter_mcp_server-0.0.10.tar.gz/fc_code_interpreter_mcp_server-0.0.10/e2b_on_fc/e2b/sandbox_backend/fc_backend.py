import logging
import os
import random
import string
from typing import List
from typing import Optional

from alibabacloud_credentials.client import Client as CredentialClient, ac
from alibabacloud_fc20230330 import models as fc20230330_models
from alibabacloud_fc20230330.client import Client as FC20230330Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from e2b.sandbox.sandbox_api import ListedSandbox, SandboxState

logger = logging.getLogger(__name__)

F_PREFIX="e2b-sandbox"

class FCBackend:
    def __init__(
        self,
        endpoint: Optional[str] = None
    ):
        self.ENDPOINT = os.getenv("ENDPOINT") 
        self.E2B_IMAGE = os.getenv("E2B_IMAGE")
        self.LOG_STORE = os.getenv("LOG_STORE")
        self.LOG_PROJECT = os.getenv("LOG_PROJECT")
        self.SECURITY_GROUP_ID = os.getenv("SECURITY_GROUP_ID")
        self.V_SWITCH_ID = os.getenv("V_SWITCH_ID")
        self.VPC_ID = os.getenv("VPC_ID")

        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        credential = CredentialClient()
        config = open_api_models.Config(
            credential=credential
        )
        # Endpoint 请参考 https://api.aliyun.com/product/FC
        if endpoint is not None:
            config.endpoint = endpoint
        else:
            config.endpoint = self.ENDPOINT
        self.client = FC20230330Client(config)

    
    def list(
        self
    ) -> List[ListedSandbox]:
        """
        List all running sandboxes.
        :return: List of running sandboxes
        """

        response = self._list_functions()
        return [
            ListedSandbox(
                sandbox_id=func.function_name,
                template_id=func.custom_container_config.image,
                name=func.function_name,
                metadata=None,
                state=func.state,
                cpu_count=func.cpu,
                memory_mb=func.memory_size,
                started_at=func.created_time,
                end_at=None,
            )
            for func in response.body.functions
        ]

    def _create_function(
        self,
        customeImage: Optional[str] = None,
        log_store: Optional[str] = None,
        log_project: Optional[str] = None,
        security_group_id: Optional[str] = None,
        v_switch_id: Optional[str] = None,
        vpc_id: Optional[str] = None,
        cpu: Optional[float] = 0.35,
        memory: Optional[int] = 512,
    ) -> fc20230330_models.CreateFunctionResponse:
        function_name = f"{F_PREFIX}-{''.join(random.choices(string.ascii_letters + string.digits, k=6))}"
        
        if log_store is not None:
            self.LOG_STORE = log_store
        if log_project is not None:
            self.LOG_PROJECT = log_project
        if security_group_id is not None:
            self.SECURITY_GROUP_ID = security_group_id
        if v_switch_id is not None: 
            self.V_SWITCH_ID = v_switch_id
        if vpc_id is not None:
            self.VPC_ID = vpc_id

        create_function_input_log_config = None
        if self.LOG_STORE and self.LOG_PROJECT and self.LOG_STORE.strip() and self.LOG_PROJECT.strip():
            create_function_input_log_config = fc20230330_models.LogConfig(
                logstore=self.LOG_STORE,
                project=self.LOG_PROJECT,
                enable_request_metrics=True,
                enable_instance_metrics=True,
                log_begin_rule='DefaultRegex'
            )
         
        create_function_input_vpc_config = None
        if self.VPC_ID and self.V_SWITCH_ID and self.SECURITY_GROUP_ID:
            create_function_input_vpc_config = fc20230330_models.VPCConfig(
                security_group_id=self.SECURITY_GROUP_ID,
                v_switch_ids=[
                    self.V_SWITCH_ID
                ],
                vpc_id=self.VPC_ID
            )
        
        if customeImage is not None:
            self.E2B_IMAGE = customeImage

        create_function_input_custom_container_config = fc20230330_models.CustomContainerConfig(
            image=self.E2B_IMAGE,
            port=5000
        )

        # 构建CreateFunctionInput，只包含有效的配置
        create_function_input_kwargs = {
            'handler': 'index.handler',
            'runtime': 'custom-container',
            'function_name': function_name,
            'custom_container_config': create_function_input_custom_container_config,
            'timeout': 60,
            'instance_concurrency': 20,
            'memory_size': memory,
            'disk_size': 512,
            'internet_access': True,
            'cpu': cpu
        }
        
        # 只有当配置有效时才添加可选参数
        if create_function_input_log_config is not None:
            create_function_input_kwargs['log_config'] = create_function_input_log_config
        if create_function_input_vpc_config is not None:
            create_function_input_kwargs['vpc_config'] = create_function_input_vpc_config
            
        create_function_input = fc20230330_models.CreateFunctionInput(**create_function_input_kwargs)
        create_function_request = fc20230330_models.CreateFunctionRequest(
            body=create_function_input
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.create_function_with_options(create_function_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise            

    def _create_trigger(
        self,
        function_name: str,
    ) -> fc20230330_models.CreateTriggerResponse:
        trigger_name = f"{function_name}-triiger-{''.join(random.choices(string.ascii_letters + string.digits, k=6))}" 
        create_trigger_input = fc20230330_models.CreateTriggerInput(
            trigger_type='http',
            trigger_name=trigger_name,
            trigger_config='{"disableURLInternet": false,"methods": ["GET", "POST", "PUT", "DELETE"],"authType": "anonymous"}'
        )
        create_trigger_request = fc20230330_models.CreateTriggerRequest(
            body=create_trigger_input
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.create_trigger_with_options(function_name, create_trigger_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise               

    def _put_concurrency_config(
        self,
        function_name: str,
    ) -> fc20230330_models.PutConcurrencyConfigResponse:
        put_concurrency_input = fc20230330_models.PutConcurrencyInput(
            reserved_concurrency=1
        )
        put_concurrency_config_request = fc20230330_models.PutConcurrencyConfigRequest(
            body=put_concurrency_input
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        max_retries = 60
        for attempt in range(max_retries):
            try:
                response = self.client.put_concurrency_config_with_options(function_name, put_concurrency_config_request, headers, runtime)
                return response
            except Exception as error:
                if getattr(error, 'code', None) == 'ConcurrentUpdateError' and attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                logger.exception(error)
                raise
    def _delete_concurrency_config(
        self,
        function_name: str,
    ) -> fc20230330_models.PutConcurrencyConfigResponse:
        runtime = util_models.RuntimeOptions()
        headers = {}
        max_retries = 60
        for attempt in range(max_retries):
            try:
                response = self.client.delete_concurrency_config_with_options(function_name,  headers, runtime)
                return response
            except Exception as error:
                if getattr(error, 'code', None) == 'ConcurrentUpdateError' and attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                # logger.exception(error)
                raise
    
    def _list_concurrency_config(       
        self,
        function_name: str,
    ) -> fc20230330_models.ListConcurrencyConfigsRequest:
        list_concurrency_configs_request = fc20230330_models.ListConcurrencyConfigsRequest(
            function_name=function_name
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.list_concurrency_configs_with_options(list_concurrency_configs_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise
            
    def _get_concurrency_config(
        self,
        function_name: str,
    ) -> fc20230330_models.GetConcurrencyConfigResponse:
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            responese = self.client.get_concurrency_config_with_options(function_name, headers, runtime)
            return responese
        except Exception as error:
            logger.exception(error)
            raise
    def _put_provision_config(
        self,
        function_name: str,
    ) -> fc20230330_models.PutProvisionConfigResponse:
        put_provision_config_input = fc20230330_models.PutProvisionConfigInput(
            target=1
        )
        put_provision_config_request = fc20230330_models.PutProvisionConfigRequest(
            body=put_provision_config_input
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.put_provision_config_with_options(function_name, put_provision_config_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise
            
    def _delete_trigger(
        self,
        function_name: str,
        trigger_name: str,
    ) -> fc20230330_models.DeleteTriggerResponse:
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.delete_trigger_with_options(function_name, trigger_name, headers, runtime)
            return response
        except Exception as error:
            # logger.exception(error)
            raise
            

    def _delete_provision_config(
        self,
        function_name: str,
    ) -> fc20230330_models.DeleteProvisionConfigResponse:
        delete_provision_config_request = fc20230330_models.DeleteProvisionConfigRequest()
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.delete_provision_config_with_options(function_name, delete_provision_config_request, headers, runtime)
            return response
        except Exception as error:
            # logger.exception(error)
            raise
            

    def _get_provision_config(
        self,
        function_name: str,
    ) -> fc20230330_models.GetProvisionConfigResponse:
        get_provision_config_request = fc20230330_models.GetProvisionConfigRequest()
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.get_provision_config_with_options(function_name, get_provision_config_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise
            

    def _list_instances(
        self,
        function_name: str,
    ) -> fc20230330_models.ListInstancesResponse:
        list_instances_request = fc20230330_models.ListInstancesRequest(
            # instance_status=[
            #     'Running'
            # ]
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.list_instances_with_options(function_name, list_instances_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise
            
    def _delete_function(
        self,
        function_name: str,
    ) -> fc20230330_models.DeleteFunctionResponse:
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            responese = self.client.delete_function_with_options(function_name, headers, runtime)
            return responese
        except Exception as error:
            # logger.exception(error)
            raise
            

    def _list_functions(
        self,
    ) -> fc20230330_models.ListFunctionsResponse:
        list_functions_request = fc20230330_models.ListFunctionsRequest(
            prefix=F_PREFIX,
            limit=100
        )
        runtime = util_models.RuntimeOptions()
        headers = {}
        try:
            response = self.client.list_functions_with_options(list_functions_request, headers, runtime)
            return response
        except Exception as error:
            logger.exception(error)
            raise
    def _list_triggers(
        self,
        sandbox_id: str,
    ) -> fc20230330_models.ListTriggersResponse:
        list_triggers_request = fc20230330_models.ListTriggersRequest()
        runtime = util_models.RuntimeOptions(
            read_timeout=60000
        )
        headers = {
            "x-fc-disable-list-remote-eb-triggers": "true",
            "x-fc-disable-list-remote-alb-triggers": "true"
        }
        try:
            response = self.client.list_triggers_with_options(sandbox_id, list_triggers_request, headers, runtime)
            return response
                
        except Exception as error:
            logger.exception(error)
            raise