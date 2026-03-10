from django.apps import AppConfig


class SmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sms'
    verbose_name = '手机短信管理'
