from dataclasses import dataclass, field, asdict
from django.utils.timezone import now
from django.utils import dateparse
from typing import List, Literal, TypedDict
from time import time
from enum import Enum
from uuid import uuid4
from dm_core.crypto.asymmetric import AsymmetricCrypto
from .auth_app_client import AuthzAppClient
from .errors import GET_ERROR
from .service import MetaClient
from .exceptions import RestAuthenticationException, RestPermissionException
import re
import logging

logger = logging.getLogger()


def uuid_generator():
    return uuid4().hex


class UserType(Enum):
    INTERNAL = 'INTERNAL'
    EXTERNAL = 'EXTERNAL'
    ANONYMOUS = 'ANONYMOUS'


class ExternalUserPermissionDict(TypedDict):
    app: str
    permission: str
    permitted_auth_types: List[str]


@dataclass
class AnonymousUser(object):

    id: str = field(default='AnonymousUser')

    def authenticate(self, *args, **kwargs):
        return True

    def permissions(self, *args, **kwargs):
        pass


@dataclass
class InternalUser(object):

    source_service: str
    encrypted_hash: str
    timestamp: str

    def __post_init__(self):
        self.timeout = 30

    def permissions(self, *args, **kwargs) -> bool:
        """
        Internal user does not require authorization
        """
        return True

    def authenticate(self, request, *args, **kwargs):
        try:
            if not self._verify_sign(request, self.source_service, self.encrypted_hash, self.timestamp):
                raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA008'))
        except ValueError:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA009'))
        if time() > int(self.timestamp) + self.timeout:
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA012'))

    def _verify_sign(self, request, auth_source_service, auth_encrypted_hash, auth_timestamp):
        hashable_text = self._prepare_hashable_data(request, auth_timestamp)
        public_key = self._get_public_key(auth_source_service)
        if public_key is None:
            return False
        return AsymmetricCrypto(public_key=public_key).verify_sign(hashable_text.encode(), bytes.fromhex(auth_encrypted_hash))

    def _prepare_hashable_data(self, request, auth_timestamp):
        """
        Preparing hashable data just like in dm_core.tracer service.py Requests class
        """
        hashable_text = request.get_full_path()
        hashable_text += auth_timestamp
        if request.body is not None:
            hashable_text += request.body.decode()
        return hashable_text

    def _get_public_key(self, auth_source_service):
        try:
            service_response = MetaClient().service_info(auth_source_service, cache_key=auth_source_service)
            return service_response['public_key']
        except:
            return None


@dataclass
class ExternalUser(object):

    session: str
    expires: str
    application: str
    user: str
    raw_data: bytes = None
    resource: str = None
    resource_type: str = None
    group: str = None
    permission: str = None
    uuid: str = field(default_factory=uuid_generator)

    def __eq__(self, other):
        return self.session == other.session and self.uuid == other.uuid

    @classmethod
    def build(cls, **kwargs):
        return cls(**kwargs)

    def to_dict(self):
        return asdict(self)

    def permissions(self, consumers: List[ExternalUserPermissionDict], *args, **kwargs):
        """
        Permission check api's external_consumer permission vs user's permission list
        """
        # resource_type = None is also allowed as 'None'
        api_permissions = list(filter(lambda kv: kv['app'] == self.application and str(self.resource_type) in kv['permitted_auth_types'], consumers))
        if len(api_permissions) != 1:
            raise RestPermissionException(detail=GET_ERROR('DMCLIENTMETA011'))
        api_permission = api_permissions[0]['permission']
        if not api_permission:
            # If api_permission is empty or None, then api's external_consumer is not expecting any permission check
            return
        self._permission_match(api_permission, self.permission)

    def authenticate(self):
        is_valid = AuthzAppClient(self.application).validate_signature(self.raw_data['data'], self.raw_data['sign'])
        if not is_valid:
            return RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA008'))
        if dateparse.parse_datetime(self.expires) < now():
            raise RestAuthenticationException(detail=GET_ERROR('DMCLIENTMETA007'))
        return None

    def _permission_match(self, api_permission: str, user_permission: str) -> bool:
        """
        Try to match the user_permissions with api_permission
        """
        if user_permission is not None:
            if type(user_permission) == list:
                raise TypeError('Expect user_permission should be string, created by AuthzAppClientService().get_permissions_expression()')
            if re.match(user_permission, api_permission):
                return True
        raise RestPermissionException(detail=GET_ERROR('DMCLIENTMETA011'))