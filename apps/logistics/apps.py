from django.apps import AppConfig
from django.contrib import admin


class LogisticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.logistics'
    verbose_name = '物流管理'

    def ready(self):
        """应用就绪时自动注册模型到Admin"""
        from .models import LogisticsChannel, LogisticsRecord, LogisticsTrace
        from .admin import LogisticsChannelAdmin, LogisticsRecordAdmin, LogisticsTraceAdmin
        
        # 注册到admin site
        if not admin.site.is_registered(LogisticsChannel):
            admin.site.register(LogisticsChannel, LogisticsChannelAdmin)
        if not admin.site.is_registered(LogisticsRecord):
            admin.site.register(LogisticsRecord, LogisticsRecordAdmin)
        if not admin.site.is_registered(LogisticsTrace):
            admin.site.register(LogisticsTrace, LogisticsTraceAdmin)
