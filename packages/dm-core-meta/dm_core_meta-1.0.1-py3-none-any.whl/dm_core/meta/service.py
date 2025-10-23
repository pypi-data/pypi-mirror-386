from abc import ABC
from django.conf import settings
from django import http
from jsonschema import Draft7Validator
from rest_framework import status
from dm_core.meta import exceptions
from dm_core.redis.service import cache
from dm_core.tracer.service import Requests
from dm_core.redis.utils import singleton
from urllib.parse import urlparse
from urllib.parse import parse_qs
import logging
import re
import time

logger = logging.getLogger()


@singleton
class MetaClient(object):

    def __init__(self):
        config = settings.DM_META_CLIENT_SETTINGS
        assert ('meta_service' in config)
        assert ('meta_port' in config)
        assert ('token' in config)
        self.url = '{}:{}'.format(config['meta_service'], config['meta_port'])
        self.meta_service = 'meta'
        self.service = settings.SERVICE
        self.path = {
            'core.service-info': f"service/{self.meta_service}/" + 'core/internal/service-info/{service}/v1',
            'core.my-service-info': f"service/{self.meta_service}/" + 'core/internal/my-service-info/v1',
            'rest-api.detailed': f"service/{self.meta_service}/" + 'rest-api/internal/detail/{rest_id}/v1',
            'rest-api.consumer': f"service/{self.meta_service}/" + 'rest-api/internal/consumer/{consumer}/v1',
            'rest-api.provider': f"service/{self.meta_service}/" + 'rest-api/internal/provider/{provider}/v1',
            'rest-api.auth-application': f"service/{self.meta_service}/" + 'rest-api/internal/auth/{name}/v1',
            'message-broker.destination-queue': f"service/{self.meta_service}/" + 'message/internal/queue/v1',
            'message-broker.source-message': f"service/{self.meta_service}/" + 'message/internal/source/{exchange_key}/v1',
            'message-broker.destination-message': f"service/{self.meta_service}/" + 'message/internal/destination/{exchange_key}/v1',
            'clear-schema-cache': f"service/{self.meta_service}/" + 'core/internal/clear-schema-cache/v1',
            'maintenance': f"service/{self.meta_service}/" + 'core/internal/maintenance/v1',
            'system-events-disable': f"service/{self.meta_service}/" + 'core/internal/system-events-disable/v1',
        }
        self.headers = {
            'Authorization': 'Token {}'.format(config['token']),
            'Content-Type': 'application/json'
        }

    def _requests(self, rest_id, rest_method, rest_url, headers, *args, **kwargs):
        while True:
            try:
                response, request = Requests(self.meta_service, rest_id)(rest_method, rest_url, headers=dict(headers), **kwargs)
            except ConnectionError as e:
                logger.info(e)
                logger.info('Error connecting to service {}, sleeping for 5 seconds'.format(self.meta_service))
                time.sleep(5)
            else:
                return response, request

    @cache('meta.my-service-info')
    def my_service_info(self, **kwargs):
        if len(kwargs) > 0 and 'cache_key' in kwargs:
            raise exceptions.MetaCacheKeyNotRequiredException(['Extra kwargs are unexpected'])
        url = 'http://{}/{}'.format(self.url, self.path['core.my-service-info'])
        response, request = self._requests('core.my-service-info', 'GET', url, headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'core.my-service-info')
        return response.json()

    @cache('meta.service-info')
    def service_info(self, service, **kwargs):
        if 'cache_key' not in kwargs or kwargs['cache_key'] != service:
            raise exceptions.MetaCacheKeyRequiredException(['cache_key not defined. Sent named parameters: ' + str(kwargs)])
        url = 'http://{}/{}'.format(self.url, self.path['core.service-info'])
        response, request = self._requests('core.service-info', 'GET', url.format(service=service), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK)
        return response.json()

    @cache('meta.rest-api.id')
    def get_restapi(self, rest_id, **kwargs):
        if 'cache_key' not in kwargs or kwargs['cache_key'] != rest_id:
            raise exceptions.MetaCacheKeyRequiredException([f"cache_key should be defined and set to ${rest_id}. Sent named parameters: " + str(kwargs)])
        url = 'http://{}/{}'.format(self.url, self.path['rest-api.detailed'])
        response, request = self._requests('rest-api.detailed', 'GET', url.format(rest_id=rest_id), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'rest-api.detailed')
        return response.json()

    @cache('meta.rest-api.consumer')
    def retrieve_rest_consumer(self, **kwargs):
        if len(kwargs) > 0  and 'cache_key' in kwargs:
            raise exceptions.MetaCacheKeyNotRequiredException(['Extra kwargs are unexpected'])
        url = 'http://{}/{}'.format(self.url, self.path['rest-api.consumer'])
        response, request = self._requests('rest-api.consumer', 'GET', url.format(consumer=self.service), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'rest-api.consumer')
        return response.json()

    @cache('meta.rest-api.provider')
    def retrieve_rest_provider(self, **kwargs):
        if len(kwargs) > 0  and 'cache_key' in kwargs:
            raise exceptions.MetaCacheKeyNotRequiredException(['Extra kwargs are unexpected'])
        url = 'http://{}/{}'.format(self.url, self.path['rest-api.provider'])
        response, request = self._requests('rest-api.provider', 'GET', url.format(provider=self.service), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'rest-api.provider')
        return response.json()

    @cache('meta.message-broker.destination-queue')
    def get_destination_queue(self, **kwargs):
        if len(kwargs) > 0 and 'cache_key' in kwargs:
            raise exceptions.MetaCacheKeyNotRequiredException(['Extra kwargs are unexpected'])
        url = 'http://{}/{}'.format(self.url, self.path['message-broker.destination-queue'])
        response, request = self._requests('message-broker.destination-queue', 'GET', url, headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'message-broker.destination-queue')
        return response.json()

    @cache('meta.message-broker.source-message')
    def get_source_message(self, exchange_key, **kwargs):
        if 'cache_key' not in kwargs or kwargs['cache_key'] != exchange_key:
            raise exceptions.MetaCacheKeyRequiredException(
                [f"cache_key should be defined and set to ${exchange_key}. Sent named parameters: " + str(kwargs)])
        url = 'http://{}/{}'.format(self.url, self.path['message-broker.source-message'])
        response, request = self._requests('message-broker.source-message', 'GET', url.format(exchange_key=exchange_key), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'message-broker.source-message')
        return response.json()

    @cache('meta.message-broker.destination-message')
    def get_destination_message(self, exchange_key, **kwargs):
        if 'cache_key' not in kwargs or kwargs['cache_key'] != exchange_key:
            raise exceptions.MetaCacheKeyRequiredException([f"cache_key should be defined and set to ${exchange_key}. Sent named parameters: " + str(kwargs)])
        url = 'http://{}/{}'.format(self.url, self.path['message-broker.destination-message'])
        response, request = self._requests('message-broker.destination-message', 'GET', url.format(exchange_key=exchange_key), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'message-broker.destination-message')
        return response.json()

    @cache('meta.rest-api.auth-application')
    def get_auth_application(self, name, **kwargs):
        if 'cache_key' not in kwargs or kwargs['cache_key'] != name:
            raise exceptions.MetaCacheKeyRequiredException(
                [f"cache_key should be defined and set to ${name}. Sent named parameters: " + str(kwargs)])
        url = 'http://{}/{}'.format(self.url, self.path['rest-api.auth-application'])
        response, request = self._requests('rest-api.auth-application', 'GET', url.format(name=name), headers=self.headers)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'rest-api.auth-application')
        return response.json()

    def core_internal_clean_schema_cache(self, **kwargs):
        """
        Used to clear cache meta schema
        """
        # @cache not required
        url = 'http://{}/{}'.format(self.url, self.path['clear-schema-cache'])
        response, request = self._requests('internal.clear-schema-cache', 'GET', url, headers=self.headers, **kwargs)
        exceptions.meta_handle_exceptions(response, status.HTTP_200_OK, 'internal.clear-schema-cache')
        return response, request

    def core_internal_maintenance(self, status: bool,  **kwargs):
        """
        Used to set maintenance mode on/off
        """
        url = 'http://{}/{}'.format(self.url, self.path['maintenance'])
        data = {
            'status': status
        }
        response, request = self._requests('internal.maintenance', 'POST', url, headers=self.headers, json=data, **kwargs)
        exceptions.meta_handle_exceptions(response, 200, 'internal.maintenance')
        return response, request

    def core_internal_system_events_disable(self, status: bool, **kwargs):
        """
        Used to enable system events in scheduler service
        """
        url = 'http://{}/{}'.format(self.url, self.path['system-events-disable'])
        data = {
            'status': status
        }
        response, request = self._requests('internal.system-events-disable', 'POST', url, headers=self.headers, json=data, **kwargs)
        exceptions.meta_handle_exceptions(response, 200, 'internal.system-events-disable')
        return response, request


class ValidatorAbc(ABC):

    """Abstract validator class to be used by ApiValidator and MessageValidator classes"""
    @classmethod
    def _validate_json(cls, json_schema, json_data):
        validator = Draft7Validator(json_schema)
        errors = sorted(validator.iter_errors(json_data), key=lambda e: e.path)
        if len(errors) > 0:
            return list(map(lambda x: '#{} => {}'.format(x.json_path, x.message), errors))
        return None


class ApiValidator(ValidatorAbc):

    def __init__(self, api_id):
        self.rest_api_spec = MetaClient().get_restapi(api_id, cache_key=api_id)

    def validate(self, request, view_object):
        self.validate_header(request)
        params_serializer = self.validate_param_serializer(request, view_object)
        self.validate_params(request)
        input_serializer = self.validate_request_serializer(request.data, view_object)
        self.validate_request(request.data)
        return input_serializer, params_serializer

    def validate_header(self, request: http.request):
        if not re.match(f"/service/{settings.SERVICE}" + self.rest_api_spec['url_inbound'], request.get_full_path()):
            raise exceptions.RestNotFoundException()
        if self.rest_api_spec['method'] != request.method:
            raise exceptions.RestMethodNotAllowedException(request.method)

    def validate_request_serializer(self, data, view_object):
        """
        Invoke serializer, validate the data, raise expecptions if any and store the results back to view object
        """
        context = view_object.get_context() if hasattr(view_object, 'get_context') else {}
        serializer = None
        if hasattr(view_object, 'get_input_serializer_instance'):
            serializer = view_object.get_input_serializer_instance()
        elif hasattr(view_object, 'input_serializer_class'):
            serializer_class = view_object.input_serializer_class
            if serializer_class is not None:
                serializer = serializer_class(data=data, context=context)
        elif hasattr(view_object, 'get_input_serializer_class'):
            serializer_class = view_object.get_input_serializer_class()
            if serializer_class is not None:
                serializer = serializer_class(data=data, context=context)
        if serializer is not None:
            serializer.is_valid(raise_exception=True)
            return serializer
        return None

    def validate_request(self, data):
        errors = self._validate_json(self.rest_api_spec['request_validator']['body'], data)
        if errors is not None and len(errors) > 0:
            raise exceptions.SchemaValidationException(errors)

    def validate_param_serializer(self, request, view_object):
        if hasattr(view_object, 'params_serializer_class') or hasattr(view_object, 'get_params_serializer_class'):
            if hasattr(view_object, 'params_serializer_class'):
                param_serializer_class = view_object.params_serializer_class
            else:
                param_serializer_class = view_object.get_params_serializer_class()
            params = urlparse(request.get_full_path())
            data = parse_qs(params.query)
            mapped_data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
            if param_serializer_class is not None:
                param_serializer_instance = param_serializer_class(data=mapped_data)
                if not param_serializer_instance.is_valid():
                    raise exceptions.RestInvalidInputException(param_serializer_instance.errors)
                request.dm_query_params = param_serializer_instance.validated_data
                return param_serializer_instance
        request.dm_query_params = {}
        return None

    def validate_params(self, request):
        params = urlparse(request.get_full_path())
        if len(params.query) > 0 and 'params' in self.rest_api_spec['request_validator']:
            data = parse_qs(params.query)
            mapped_data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
            errors = self._validate_json(self.rest_api_spec['request_validator']['params'], mapped_data)
            if errors is not None and len(errors) > 0:
                raise exceptions.RestInvalidInputException(errors)
        return None

    def validate_response(self, data, resp_status, restapi_id, raise_unknown_response_status=False):
        resp_status = str(resp_status)
        status_key = self._find_matching_pattern(resp_status, self.rest_api_spec['response_validator'])
        if raise_unknown_response_status is True:
            if status_key is None:
                rest_id = 'REST ID: {} Received:{} Expected:{}. '.format(restapi_id, resp_status,
                                                                list(self.rest_api_spec['response_validator'].keys()))
                raise exceptions.UndefinedResponseStatusException([rest_id, data])
        if status_key is not None:
            errors = self._validate_json(self.rest_api_spec['response_validator'][status_key], data)
            if errors is not None and len(errors) > 0:
                rest_detail = ['REST ID: {} Received {} Expected {}. '.format(restapi_id, resp_status, list(self.rest_api_spec['response_validator'].keys()))]
                raise exceptions.SchemaValidationException(rest_detail + errors)
        return None

    def _find_matching_pattern(self, x, patterns):
        for pattern in patterns:
            if pattern.endswith('xx'):
                # Convert '2xx' to regex pattern '^2\d\d$' for matching 200-299
                regex = re.compile(f"^{pattern[0]}\\d{{2}}$")
                if regex.match(x):
                    return pattern
            elif x == pattern:
                return pattern
        return None