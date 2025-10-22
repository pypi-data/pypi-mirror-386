from dm_core.meta.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from .models import AppConfigModel


class AbstractSerializer(object):
    """
    Abstract serializer: This serializer should be inherited by all serializers to avoid additional fields being passed
    """

    def additional_parameter_found_exception(self, field_keys: dict, initial_data: dict, path=''):
        allowed_fields = set(field_keys.keys())
        input_fields = set(initial_data.keys())

        # Find unexpected fields
        unexpected_fields = input_fields - allowed_fields
        if unexpected_fields:
            raise ValidationError({
                f"{path}{'errors' if not path else ''}": [
                    _(f"Unexpected field(s) found: {', '.join(unexpected_fields)}")
                ]
            })

        # Recursively validate nested serializers
        for key in allowed_fields & input_fields:
            field = field_keys[key]
            value = initial_data[key]
            if isinstance(field, serializers.BaseSerializer) and isinstance(value, dict):
                # Recurse into nested serializer
                self.additional_parameter_found_exception(field.fields, value, path=f"{path}.{key}" if path else key)

    def to_internal_value(self, data):
        # Check for unexpected fields, useful when inner nested serializer
        allowed_keys = set(self.fields.keys())
        received_keys = set(data.keys())
        extra_keys = received_keys - allowed_keys

        if extra_keys:
            raise serializers.ValidationError({
                key: ["Unexpected field."] for key in extra_keys
            })
        return super().to_internal_value(data)


class AppConfigSerializer(serializers.ModelSerializer, AbstractSerializer):

    class Meta:
        model = AppConfigModel
        fields = ['key', 'value']
        read_only_fields = ['key']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'data' in kwargs:
            self.additional_parameter_found_exception(self.fields, kwargs['data'])


class PaginationSerializer(AbstractSerializer, serializers.Serializer):

    limit = serializers.IntegerField(default=10, min_value=1)
    offset = serializers.IntegerField(default=0)