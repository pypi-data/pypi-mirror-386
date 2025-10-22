from django.apps import AppConfig


class MetaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_core.meta'
    label = 'dm_core_meta'
