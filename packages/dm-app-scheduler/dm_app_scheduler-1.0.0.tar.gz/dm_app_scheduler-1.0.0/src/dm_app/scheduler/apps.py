from django.apps import AppConfig


class DmAppScheduleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dm_app.scheduler'
    label = 'dm_app_scheduler'
