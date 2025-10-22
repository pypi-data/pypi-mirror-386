from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.authentication import BaseAuthentication
from rest_framework import HTTP_HEADER_ENCODING
from typing import Union
from .exceptions import RestAuthenticationException, RestPermissionException
from .service import ApiValidator
from .users import ExternalUser, InternalUser, AnonymousUser
from dm_core.redis.service import RedisSessionManager
from .errors import GET_ERROR
import json


def get_authorization_header(request, header):
    """
    Return request's 'Authorization:' header, as a bytestring.
    """
    auth = request.META.get(header, b'')
    if isinstance(auth, str):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class DmAnonymousAuthentication(BaseAuthentication):
    """
    Anonymous Authentication Class required to fill DEFAULT_AUTHENTICATION_CLASSES in settings.py

    AnonymousUser is return if none of the other (InternalUser, ExternalUser) are set
    depending on header information received
    """

    def authenticate(self, request):
        return AnonymousUser(), None

    def authenticate_header(self, request):
        # Optionally provide a custom authentication header
        return 'Bearer'


class DmInternalAuthentication(BaseAuthentication):
    """
    Internal Authentication Class required to fill DEFAULT_AUTHENTICATION_CLASSES in settings.py

    InternalUser is returned if the HTTP_DM_SOURCE_SERVICE, HTTP_DM_ENCRYPTED_HASH, HTTP_DM_TIMESTAMP is set
    """

    def authenticate(self, request):
        auth_source_service = get_authorization_header(request, 'HTTP_DM_SOURCE_SERVICE').decode()
        auth_encrypted_hash = get_authorization_header(request, 'HTTP_DM_ENCRYPTED_HASH').decode()
        auth_timestamp = get_authorization_header(request, 'HTTP_DM_TIMESTAMP').decode()
        if auth_source_service and auth_encrypted_hash and auth_timestamp:
            internal_user = InternalUser(auth_source_service, auth_encrypted_hash, auth_timestamp)
            return internal_user, type(self).__name__
        return None

    def authenticate_header(self, request):
        return 'DM-SOURCE-SERVICE'


class DmExternalAuthentication(BaseAuthentication):
    """
    External Authentication Class required to fill DEFAULT_AUTHENTICATION_CLASSES in settings.py

    ExternalUser is returned if HTTP_AUTHORIZATION is set
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request, 'HTTP_AUTHORIZATION').split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA001'))
        elif len(auth) > 2:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA002'))

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA003'))

        session = self.get_session(token)
        return session, type(self).__name__

    def authenticate_header(self, request):
        return self.keyword

    def get_session(self, token):
        signed_instance = RedisSessionManager().get(token)
        if signed_instance is None:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA004'))
        return ExternalUser.build(raw_data=signed_instance, **json.loads(signed_instance['data'].decode()))


class ApiAuthenticate(object):

    def __init__(self, api_spec: ApiValidator, request: Request):
        self.api_spec = api_spec
        self.request = request

    def authenticate(self) -> Union[Response, None]:
        """
        authenticate

        Based on who you are : InternalUser, ExternalUser or AnanonymousUser in the order specified,
        authentication is performed
        """
        if isinstance(self.request.user, InternalUser):
            self._internal_user_authentication()
        elif isinstance(self.request.user, ExternalUser):
            self._external_user_authentication()
        elif isinstance(self.request.user, AnonymousUser):
            self._anonymous_user_authentication()
        else:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA005'))

    def permission(self):
        if isinstance(self.request.user, InternalUser):
            self.request.user.permissions()
        elif isinstance(self.request.user, ExternalUser):
            self.request.user.permissions(self.api_spec.rest_api_spec['external_consumers'])
        elif isinstance(self.request.user, AnonymousUser):
            self.request.user.permissions()
        else:
            raise RestPermissionException(detail=GET_ERROR('DMCLIENTMETA010'))

    def _internal_user_authentication(self):
        """
        Authenticate if the request is initiated by DM SERVICES
        """
        if self.request.user.source_service in self.api_spec.rest_api_spec['internal_consumers']:
            self.request.user.authenticate(self.request)

    def _external_user_authentication(self):
        """
        Authenticate if the request is initiated by authenticated USER
        """
        self.request.user.authenticate()


    def _anonymous_user_authentication(self):
        if self.api_spec.rest_api_spec['auth_anonymous'] is False:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA006'))

