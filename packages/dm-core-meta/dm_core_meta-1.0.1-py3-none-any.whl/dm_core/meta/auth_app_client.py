from django.conf import settings
from dm_core.crypto.asymmetric import AsymmetricCrypto
from dm_core.redis.utils import singleton_with_param
from dm_core.tracer.service import Requests, RequestAuthEnum
from requests.models import Response, Request
from .decorator import api_outbound_validator
from .service import MetaClient

@singleton_with_param
class AuthzAppClient(object):

    def __init__(self, application):
        meta_client = MetaClient()
        self.application = application
        self.service = settings.SERVICE
        self.url, self.target_service = self._authz_url(meta_client, application)
        self.public_key = meta_client.service_info(self.target_service, cache_key=self.target_service)['public_key']
        self.private_key = meta_client.my_service_info()['private_key']

    def _authz_url(self, meta_client, application):
        response_data = meta_client.get_auth_application(application, cache_key=application)
        return response_data['url'], response_data['service']

    @api_outbound_validator()
    def _api(self, service, api_id, method, url_path, *args, **kwargs) -> (Response, Request):
        response, request = Requests(service, api_id, self.private_key)(method, '{}{}'.format(self.url, url_path), *args, **kwargs)
        return response, request

    def permissions(self):
        """
        Fetch the permissions
        """
        params = {

        }
        return self._api(self.target_service, 'authz.permissions', params, request_auth=RequestAuthEnum.INTERNAL)

    def validate_signature(self, data: bytes, sign: bytes) -> bool:
        """
        Validate given data and signature
        """
        crypto = AsymmetricCrypto(public_key=self.public_key)
        return crypto.verify_sign(data, sign)
