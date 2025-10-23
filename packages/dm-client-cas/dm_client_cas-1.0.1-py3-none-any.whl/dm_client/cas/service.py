from django.conf import settings
from dm_core.meta.decorator import api_outbound_validator
from dm_core.meta.service import MetaClient
from dm_core.redis.utils import singleton_with_param
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request


@singleton_with_param
class CasClient(object):

    def __init__(self, service):
        meta_client = MetaClient()
        self.service = settings.SERVICE
        self.target_service = service
        self.url = meta_client.service_info(self.target_service, cache_key=self.target_service)['url']
        self.private_key = meta_client.my_service_info()['private_key']

    @api_outbound_validator()
    def _api(self, service, api_id, method, url_path, *args, **kwargs) -> (Response, Request):
        response, request = Requests(service, api_id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    def cas_service_client_login(self, service_url: str, ticket: str) -> (Response, Request):
        params = {
            'service': service_url,
            'ticket': ticket
        }
        return self._api(self.target_service, 'sso.cas-client.login', params=params)

    def cas_service_client_logout(self, application: str, token: str) -> (Response, Request):
        params = {
            'application': application,
        }
        data = {
            'token': token
        }
        return self._api(self.target_service, 'sso.cas-client.logout', json=data, params=params, request_auth=RequestAuthEnum.INTERNAL)