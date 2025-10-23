from django.apps import AppConfig


class RedisAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_core.redis'
    label = 'dm_core_redis'
