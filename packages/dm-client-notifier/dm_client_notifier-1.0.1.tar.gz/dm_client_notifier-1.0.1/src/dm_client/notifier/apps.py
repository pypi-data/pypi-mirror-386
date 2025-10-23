from django.apps import AppConfig


class DmNotifierClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_client.notifier'
    label = 'dm_client_notifier'
