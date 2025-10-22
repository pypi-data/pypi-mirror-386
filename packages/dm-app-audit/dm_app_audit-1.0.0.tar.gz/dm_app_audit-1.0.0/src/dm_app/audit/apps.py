from django.apps import AppConfig


class DmAppAuthzConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_app.audit'
    label = 'dm_app_audit'
