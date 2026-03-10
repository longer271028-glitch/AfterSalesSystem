from django.contrib import admin
from .models import Phone, SmsRecord


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


@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    """手机管理Admin"""

    list_display = ('name', 'model', 'formatted_user', 'phone_number', 'is_active', 'formatted_created_by', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'phone_number', 'user', 'model')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'model', 'user', 'phone_number')
        }),
        ('状态与备注', {
            'fields': ('is_active', 'remark')
        }),
        ('系统信息', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def formatted_user(self, obj):
        return get_user_name(obj.user) if obj.user else '-'
    formatted_user.short_description = '用户'

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


@admin.register(SmsRecord)
class SmsRecordAdmin(admin.ModelAdmin):
    """短信记录Admin"""

    list_display = ('phone_number', 'content_short', 'received_date', 'received_time', 'formatted_sender', 'is_read')
    list_filter = ('is_read', 'received_date')
    search_fields = ('phone_number', 'content', 'sender')
    readonly_fields = ('created_at',)
    date_hierarchy = 'received_date'

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '短信内容'

    def formatted_sender(self, obj):
        return get_user_name(obj.sender) if obj.sender else '-'
    formatted_sender.short_description = '发送人'
