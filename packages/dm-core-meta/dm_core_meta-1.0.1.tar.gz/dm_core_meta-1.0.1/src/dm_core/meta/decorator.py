from json.decoder import JSONDecodeError
from dm_core.meta.service import ApiValidator
from dm_core.meta.exceptions import exception_handler


def api_inbound_validator():
    def wrapper(view_func):
        def f(view_object, request, *args, **kwargs):
            from dm_core.meta.authentication import ApiAuthenticate
            api_id = view_object.api_id[request.method]

            # Validate Request
            api_validator = ApiValidator(api_id)
            try:
                # Authenticate and Authorize
                api_authenticator = ApiAuthenticate(api_validator, request)
                api_authenticator.authenticate()
                api_authenticator.permission()

                input_serializer, params_serializer = api_validator.validate(request, view_object)
            except Exception as e:
                    return exception_handler(e)
            else:
                response = view_func(view_object, request, serializer=input_serializer, params_serializer=params_serializer, *args, **kwargs)

            # Validate Response
            if hasattr(response, 'status_code') and hasattr(response, 'data'):
                api_validator.validate_response(response.data, response.status_code, api_validator.rest_api_spec['id'])
            return response
        return f
    return wrapper


def api_outbound_validator():
    def wrapper(func):
        def f(obj, service, api_id, url_params = {}, *args, **kwargs):
            payload = _extract_payload(kwargs)
            try:
                api_validator = ApiValidator('{}.{}'.format(service, api_id))
                api_validator.validate_request(payload)
            except Exception as e:
                response = exception_handler(e)
            else:
                url_path = f"/service/{service}" + api_validator.rest_api_spec['url_outbound'].format(**url_params)
                response, request = func(obj, service, api_id, api_validator.rest_api_spec['method'], url_path, *args, **kwargs)
            try:
                resp_validate = response.json()
            except JSONDecodeError:
                try:
                    resp_validate = response.text if len(response.text) > 0 else None
                except TypeError:
                    resp_validate = None
            finally:
                api_validator.validate_response(resp_validate, response.status_code, api_validator.rest_api_spec['id'], raise_unknown_response_status=True)
            return response, request
        return f
    return wrapper


def _extract_payload(kwargs: dict):
    if 'json' in kwargs:
        return kwargs['json']
    elif 'data' in kwargs:
        return kwargs['data']
    else:
        return {}