from dm_core.meta.users import InternalUser, ExternalUser, ExternalUserPermissionDict
from dm_core.meta.errors import GET_ERROR
from dm_core.meta.exceptions import RestAuthenticationException, RestPermissionException
from django.core.signing import TimestampSigner
from faker import Faker
from typing import List
from uuid import uuid4
import random
from model_bakery import baker


class MetaTestUtils(object):
    """
    Unit Test utility for generating users
    """

    @staticmethod
    def _get_session_id():
        signer = TimestampSigner()
        return signer.sign(uuid4().hex)

    @staticmethod
    def get_internal_user(source_service='tester', *args, **kwargs) -> InternalUser:
        internal_user = InternalUser(source_service=source_service, encrypted_hash='na', timestamp='na')
        internal_user.authenticate = lambda *args, **kwargs: True
        return internal_user

    @staticmethod
    def get_external_user(application='DMUSER', resource_type='DEFAULT', user_id=uuid4().hex[:24],
                          resource=uuid4().hex[:24], *args, **kwargs) -> ExternalUser:
        session_id = MetaTestUtils._get_session_id()
        external_user = ExternalUser(session=session_id, expires='na', application=application, user=user_id,
                                     resource_type=resource_type, resource=resource)
        external_user.authenticate = lambda *args, **kwargs: True
        if kwargs.get('permission') is None:
            # No permission assignment, hence return True on permissions method invocation
            def permissions(consumers: List[ExternalUserPermissionDict], *args, **kwargs):
                for consumer in consumers:
                    if consumer['app'] == application and str(resource_type) in consumer['permitted_auth_types']:
                        return True
                raise RestPermissionException(detail=GET_ERROR('DMCLIENTMETA011'))
            external_user.permissions = permissions
        else:
            # Assign permission
            external_user.permission = kwargs.get('permission')
        return external_user

    @staticmethod
    def fake_phone_number():
        return f'+614{random.randint(10000000, 99999999)}'
