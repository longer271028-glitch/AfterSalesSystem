from django.contrib import admin
from .models import DatabaseConfig, SystemConfig


@admin.register(DatabaseConfig)
class DatabaseConfigAdmin(admin.ModelAdmin):
    """数据库配置Admin"""

    list_display = ('name', 'db_type', 'is_active', 'created_at')
    list_filter = ('db_type', 'is_active')
    fieldsets = (
        ('基本配置', {
            'fields': ('name', 'db_type', 'is_active')
        }),
        ('MySQL配置', {
            'fields': ('mysql_host', 'mysql_port', 'mysql_user', 'mysql_password', 'mysql_database'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    """系统配置Admin"""

    list_display = ('key', 'value', 'is_public', 'updated_at')
    list_filter = ('is_public',)
    search_fields = ('key', 'description')
