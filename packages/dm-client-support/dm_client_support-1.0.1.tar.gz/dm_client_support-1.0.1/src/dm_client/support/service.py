from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request
from enum import Enum


class SupportResourceType(Enum):

    EMPLOYMENT_POST = 'EMPLOYMENT_POST'


@singleton
class SupportClient(object):

    def __init__(self):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = 'support'
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

    ############### Verify #############################

    def verify_internal_resource_create(self, resource_id: str, resource_type: str) -> (Response, Request):
        """
        Resource: Create resource
        """
        data = {'resource_id': resource_id, 'resource_type': resource_type}
        return self._api(self.target_service, 'verify.internal.resource.create', request_auth=RequestAuthEnum.INTERNAL, json=data)

    def verify_internal_resource_update(self, verifier_id: str) -> (Response, Request):
        """
        Resource: List resource
        """
        url_params = {'pk': verifier_id}
        return self._api(self.target_service, 'verify.internal.resource.update', request_auth=RequestAuthEnum.INTERNAL, url_params=url_params)

    def verify_resource_list(self, auth: str, resource_type: str, resource_id: str|None) -> (Response, Request):
        """
        Resource: List resource
        """
        data = {'resource_type': resource_type}
        if resource_id is not None:
            data['resource_id'] = resource_id
        return self._api(self.target_service, 'verify.resource.list', request_auth=RequestAuthEnum.EXTERNAL, auth=auth, params=data)
