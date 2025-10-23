from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton
class ValidatorClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'validator'
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, id, method, url_path, *args, **kwargs):
        response, request = Requests(service, id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request


    ############### Version ############################
    def version(self) -> (Response, Request):
        return self._api(self.target_service, 'version')

    ################## SCHEDULE ######################
    def schedule_internal_cleanup(self) -> (Response, Request):
        return self._api(self.target_service, 'schedule.internal.cleanup', request_auth=RequestAuthEnum.INTERNAL)

    ################ Field ##############################
    def field_internal_phone(self, phone_number: str) -> (Response, Request):
        data = {'phone_number': phone_number}
        return self._api(self.target_service, 'field.internal.phone', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def field_internal_mobile(self, mobile_number: str) -> (Response, Request):
        data = {'mobile_number': mobile_number}
        return self._api(self.target_service, 'field.internal.mobile', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def field_internal_email(self, email: str) -> (Response, Request):
        data = {'email': email}
        return self._api(self.target_service, 'field.internal.email', json=data, request_auth=RequestAuthEnum.INTERNAL)

    ################ KYC ##############################
    def kyc_internal_register_verifiee(self, schema: str, external_id: str, external_owner_id: str, external_owner_type: str, complete = None, resources = None) -> (Response, Request):
        data = {
            'schema': schema,
            'external_id': external_id,
            'external_owner_id': external_owner_id,
            'external_owner_type': external_owner_type,
        }
        if complete:
            data['complete'] = complete
        if resources:
            data['resources'] = resources
        return self._api(self.target_service, 'kyc.internal.register.verifiee', json=data, request_auth=RequestAuthEnum.INTERNAL)

    def kyc_internal_update_verifiee(self, verifiee_id: str, data: dict) -> (Response, Request):
        data = {'resources': data}
        return self._api(self.target_service, 'kyc.internal.update.verifiee', url_params={'verifiee_id': verifiee_id}, jsonify=data, request_auth=RequestAuthEnum.INTERNAL)