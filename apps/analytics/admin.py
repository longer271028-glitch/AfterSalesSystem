from django.contrib import admin
from .models import Dashboard, ChartConfig, AlertRule, AlertRecord, ReportTemplate


def get_user_name(user):
    """获取用户的姓名，优先使用 first_name + last_name，否则使用 username"""
    if user is None:
        return '-'
    if user.first_name or user.last_name:
        name = f"{user.last_name}{user.first_name}".strip()
        if not name:
            name = f"{user.first_name} {user.last_name}".strip()
        return name
    return user.username


class DashboardAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_public', 'formatted_created_by', 'created_at']
    list_filter = ['is_public']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


class ChartConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'chart_type', 'data_source', 'dashboard']
    list_filter = ['chart_type', 'data_source']


class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['rule_type', 'is_active']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


class AlertRecordAdmin(admin.ModelAdmin):
    list_display = ['rule', 'title', 'status', 'formatted_handler', 'created_at']
    list_filter = ['status', 'rule__rule_type']
    date_hierarchy = 'created_at'

    def formatted_handler(self, obj):
        return get_user_name(obj.handler) if obj.handler else '-'
    formatted_handler.short_description = '处理人'


class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'data_source', 'formatted_created_by', 'created_at']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


# 手动注册所有模型到admin.site
admin.site.register(Dashboard, DashboardAdmin)
admin.site.register(ChartConfig, ChartConfigAdmin)
admin.site.register(AlertRule, AlertRuleAdmin)
admin.site.register(AlertRecord, AlertRecordAdmin)
admin.site.register(ReportTemplate, ReportTemplateAdmin)
