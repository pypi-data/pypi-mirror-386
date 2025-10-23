from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class WorkflowClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'workflow'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs):
        response, request = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    ############### Version ############################

    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ################## BPM ##############################

    def message(self, message_name: str, correlation_keys: dict, process_instance_id: str = None, business_key: str = None,
                process_variables: dict = {}, resultEnabled = True, variablesInResultEnabled = True) -> (Response, Request):
        data = {
            "messageName": '{}.{}'.format(self.target_service, message_name),
            "correlationKeys": correlation_keys,
            "resultEnabled": resultEnabled,
            "variablesInResultEnabled": variablesInResultEnabled
        }
        if len(process_variables) > 0:
            data['processVariables'] = process_variables
        if process_instance_id is not None:
            data['processInstanceId'] = process_instance_id
        if business_key is not None:
            data['businessKey'] = business_key
        headers = {
            'operation-name': '{}.{}'.format(self.target_service, message_name)
        }
        return self._api(self.target_service, message_name, json=data, headers=headers)

    def get_process_instance_variables(self, message_name: str, process_instance_id: str) -> (Response, Request):
        headers = {
            'operation-name': '{}.{}'.format(self.target_service, message_name)
        }
        return self._api(self.target_service, message_name,
                         url_params={'process_instance_id': process_instance_id},
                         headers=headers)

    def update_process_instance_variables(self, message_name: str, process_instance_id: str, data: dict) -> (Response, Request):
        headers = {
            'operation-name': '{}.{}'.format(self.target_service, message_name)
        }
        json_data = {
            "modifications": {}
        }
        for key, value in data.items():
            json_data["modifications"][key] = {
                "value": value,
            }

        return self._api(self.target_service, message_name,
                         url_params={'process_instance_id': process_instance_id},
                         json=json_data,
                         headers=headers)
