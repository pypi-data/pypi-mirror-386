from django.apps import AppConfig


class TracerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_core.tracer'
    label = 'dm_core_tracer'
