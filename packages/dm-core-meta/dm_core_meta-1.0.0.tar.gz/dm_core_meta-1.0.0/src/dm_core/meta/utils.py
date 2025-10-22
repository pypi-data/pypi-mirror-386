import re
from jsonschema import Draft7Validator
from uuid import uuid4
from decimal import Decimal
from .exceptions import SchemaValidationException


class CaseConvert(object):

    @staticmethod
    def to_snake(string):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def to_camel(string):
        words = string.split('_')
        return ''.join(word.capitalize() for word in words)


class SchemaValidate(object):
    """
    Base class for Mongo Models
    """
    def __init__(self, schema):
        self.schema = schema
        assert (hasattr(self, 'schema'))

    def validate(self, data):
        """
        Validate the model using the scheme
        :return: (True, None) or (False, Error Descriptions)
        """
        v = Draft7Validator(self.schema)
        if v.is_valid(data) is True:
            return True
        message = []
        for error in v.iter_errors(data):
            message.append(error.message)
        raise SchemaValidationException(message)


def uuid_generator():
    return uuid4().hex

def uuid_generator_24():
    return uuid4().hex[:24]

def uuid_generator_8():
    return uuid4().hex[:8]

def serializable(obj):
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return type(obj)(serializable(v) for v in obj)
    elif isinstance(obj, Decimal):
        return float(obj)
    elif hasattr(obj, '__dict__'):
        return serializable(vars(obj))
    else:
        return obj


class DMValidator(object):

    @staticmethod
    def validate_uuid4_hex(value):
        """
        Custom Django Validator to ensure with empty string or UUID4().hex

        This should be used to refer to keys across the services. (Loosely linked foreign keys)
        """
        if value and not re.match(r'^[0-9a-fA-F]{32}$', value):
            raise ValidationError('This field must be either empty or a valid 32-character hex string.')