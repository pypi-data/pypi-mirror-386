from base64 import b64encode
from .client import WorkflowClient
import json
import logging

logger = logging.getLogger()


class UserRegistrationWorkflow(object):

    def __init__(self):
        self.workflow = WorkflowClient()

    def message_initiate(self, data: dict, mobile_secret: str, email_secret: str, request_count: str):
        process_variables = {'mobile_secret': {"value": mobile_secret, "type": "String"},
                             'email_secret': {"value": email_secret, "type": "String"},
                             'request_count': {"value": request_count, "type": "Integer"},
                             'data': {"value": b64encode(json.dumps(data).encode('utf-8')).decode(),
                                      "type": "Bytes"}}
        response, _ = WorkflowClient().message('internal.message.user-register-initiate',
                                               correlation_keys={},
                                               process_variables=process_variables,
                                               resultEnabled=True, variablesInResultEnabled=False)
        return response

    def message_finalise(self, token):
        response, _ = WorkflowClient().message('internal.message.user-register-finalise',
                                               process_instance_id=token,
                                               correlation_keys={},
                                               process_variables={},
                                               resultEnabled=True, variablesInResultEnabled=True)
        return response

    def get_secrets(self, token: str):
        response, _ = WorkflowClient().get_process_instance_variables('internal.variables.get.user-register',
                                                                      process_instance_id=token)
        return response

    def update_secret(self, token: str, mobile_secret: str, email_secret: str, request_count: int):
        data = {
            'mobile_secret': mobile_secret,
            'email_secret': email_secret,
            'request_count': request_count
        }
        response, _ = WorkflowClient().update_process_instance_variables('internal.variables.update.user-register',
                                                                         process_instance_id=token,
                                                                         data=data)
        return response

    def update_security(self, token: str, password: str):
        process_variables = {
            'password': {'value': password, 'type': 'String'}
        }
        response, _ = WorkflowClient().message('internal.message.user-register-security',
                                               process_instance_id=token,
                                               correlation_keys={},
                                               process_variables=process_variables,
                                               resultEnabled=False, variablesInResultEnabled=False)
        return response

    def update_security_recovery(self, token: str, security: str):
        process_variables = {
            'security': {"value": b64encode(json.dumps(security).encode('utf-8')).decode(),
                                      "type": "Bytes"}
        }
        response, _ = WorkflowClient().message('internal.message.user-register-security-recovery',
                                               process_instance_id=token,
                                               correlation_keys={},
                                               process_variables=process_variables,
                                               resultEnabled=False, variablesInResultEnabled=False)
        return response