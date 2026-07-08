from django.contrib import admin
from .models import WorkflowType, WorkflowNode, WorkflowInstance, WorkflowTask, Organization, Role, UserProfile
from core.admin_utils import get_user_name


class WorkflowTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']


class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'name', 'node_type', 'order']
    list_filter = ['workflow', 'node_type']
    ordering = ['workflow', 'order']


class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'title', 'status', 'formatted_initiator', 'created_at']
    list_filter = ['status', 'workflow']
    date_hierarchy = 'created_at'

    def formatted_initiator(self, obj):
        return get_user_name(obj.initiator)
    formatted_initiator.short_description = '发起人'


class WorkflowTaskAdmin(admin.ModelAdmin):
    list_display = ['instance', 'node', 'formatted_assignee', 'status', 'assigned_at']
    list_filter = ['status', 'assigned_at']
    date_hierarchy = 'assigned_at'

    def formatted_assignee(self, obj):
        return get_user_name(obj.assignee)
    formatted_assignee.short_description = '处理人'


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'formatted_manager', 'is_active']
    list_filter = ['is_active']

    def formatted_manager(self, obj):
        return get_user_name(obj.manager) if obj.manager else '-'
    formatted_manager.short_description = '负责人'


class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active']
    list_filter = ['is_active']


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['formatted_user', 'organization', 'employee_no', 'phone', 'is_active']
    list_filter = ['is_active', 'organization']
    filter_horizontal = ['roles']

    def formatted_user(self, obj):
        return get_user_name(obj.user)
    formatted_user.short_description = '用户'


# 手动注册所有模型到admin.site
admin.site.register(WorkflowType, WorkflowTypeAdmin)
admin.site.register(WorkflowNode, WorkflowNodeAdmin)
admin.site.register(WorkflowInstance, WorkflowInstanceAdmin)
admin.site.register(WorkflowTask, WorkflowTaskAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
