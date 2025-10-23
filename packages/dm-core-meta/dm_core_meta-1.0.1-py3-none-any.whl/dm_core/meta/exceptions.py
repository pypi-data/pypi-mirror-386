from django.utils.translation import gettext_lazy as _
from django.db import connections
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, MethodNotAllowed, NotFound
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
import logging

logger = logging.getLogger()


class SchemaValidationException(Exception):
    """
    Exception for json schema response validation
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'SCHEMA_EXCEPTION'
    default_detail = 'Invalid schema exception'

    def __init__(self, errors):
        # Call the base class constructor with the parameters it needs
        super().__init__(errors)


class UndefinedResponseStatusException(Exception):

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'UNDEFINED_STATUS'
    default_detail = 'Invalid response status'

    """
    Exception for undefined response status

    Used in api_outbound_validator: Internally when services invoke other services and receive unexpected response
    we raise UndefinedResponseStatusException
    """
    def __init__(self, errors):
        super().__init__(errors)


class RestNotFoundException(NotFound):
    """
    Exception for API not found
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'NOT_FOUND'
    default_detail = 'Invalid request'

    def __init__(self, detail=None, status_code=None):
        super().__init__(detail, status_code)


class RestInvalidInputException(ValidationError):
    """
    Exception for API not found
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'BAD_REQUEST'
    default_detail = 'Invalid input'

    def __init__(self, detail=None, status_code=None):
        super().__init__(detail, status_code)


class RestMethodNotAllowedException(MethodNotAllowed):
    """
    Exception for not allowed method
    """

    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _('Method "{method}" not allowed.')
    default_code = 'method_not_allowed'

    def __init__(self, method, detail=None, code=None):
        super().__init__(method, detail, code)


class RestAuthenticationException(AuthenticationFailed):

    """
    Exception for Authentication
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'AUTHENTICATION_FAILED'
    default_detail = 'Request unauthorized'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RestPermissionException(PermissionDenied):

    """
    Exception for permission
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'AUTHORIZATION_FAILED'
    default_detail = 'Request unauthorized'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MetaAuthenticationException(Exception):

    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = 'AUTHENTICATION_FAILED'
    default_detail = 'Request unauthorized'

    """
    Exception for API Validation for 401
    """
    def __init__(self, errors):
        super().__init__(errors)


class MetaPermissionDeniedException(Exception):

    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'AUTHORIZATION_FAILED'
    default_detail = 'Request unauthorized'
    """
    Exception for API Validation for 403
    """
    def __init__(self, errors):
        super().__init__(errors)


class MetaUnexpectedResponseStatusException(Exception):
    """
    Exception for API Validation for unexpected
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'INTERNAL_SERVER_ERROR'
    default_detail = 'Unexpected meta response'

    def __init__(self, errors):
        super().__init__(errors)


class MetaCacheKeyRequiredException(Exception):
    """
    Exception thrown when cache_key is not defined and is requied
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'INTERNAL_SERVER_ERROR'
    default_detail = 'Cache key required'

    def __init__(self, errors):
        super().__init__(errors)


class MetaCacheKeyNotRequiredException(Exception):
    """
    Exception thrown when cache_key is not defined and is requied
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'INTERNAL_SERVER_ERROR'
    default_detail = 'Cache key not required'

    def __init__(self, errors):
        super().__init__(errors)


class MetaNotFoundException(Exception):
    """
    Exception thrown when API ID is not found
    """
    status = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_code = 'INTERNAL_SERVER_ERROR'
    default_detail = 'API Not found'

    def __init__(self, errors):
        if hasattr(errors, 'url'):
            super().__init__(f"{errors.url} not found")
        else:
            super().__init__(errors)


DM_META_EXCEPTIONS = [MetaAuthenticationException, MetaPermissionDeniedException, MetaUnexpectedResponseStatusException,
                      MetaUnexpectedResponseStatusException, MetaCacheKeyRequiredException, MetaCacheKeyNotRequiredException]

DM_EXCEPTIONS = [SchemaValidationException, UndefinedResponseStatusException, RestNotFoundException,
                 RestInvalidInputException,                 RestMethodNotAllowedException,RestAuthenticationException,
                 RestPermissionException]


def meta_handle_exceptions(response, expected_status=None, rest_id=None):
    if response.status_code == 401:
        raise MetaAuthenticationException(response)
    if response.status_code == 403:
        raise MetaPermissionDeniedException(response)
    if response.status_code == 404:
        raise MetaNotFoundException(response)
    if expected_status is not None:
        if response.status_code != expected_status:
            raise MetaUnexpectedResponseStatusException([response, rest_id])


def set_rollback():
    for db in connections.all():
        if db.settings_dict['ATOMIC_REQUESTS'] and db.in_atomic_block:
            db.set_rollback(True)


def exception_handler(exc, context=None):
    """
    Returns the response that should be used for any given exception.
    Based off rest_fraemwork.views.exception_handler

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied(detail=exc.detail)

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        if isinstance(exc.detail, (list, dict)):
            data = exc.detail
        else:
            data = {'detail': exc.detail}
        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    raise exc

    logger.warning("exception_handler unable to handle the exception")

    return None