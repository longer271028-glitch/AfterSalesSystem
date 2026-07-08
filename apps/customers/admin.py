from django.contrib import admin
from django.shortcuts import render
from django.utils.html import format_html
from django.contrib.auth.models import User
from django import forms
from django.contrib.admin.widgets import AutocompleteSelect
from .models import Customer, CustomerTag, ServiceHistory
from core.admin_utils import get_user_name, get_user_display_name


class CustomerAdminForm(forms.ModelForm):
    """客户表单 - 自定义外键字段显示"""

    class Meta:
        model = Customer
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自定义市场经理和服务经理的下拉选项，显示姓名
        for field_name in ['market_manager', 'service_manager']:
            if field_name in self.fields:
                self.fields[field_name].label_from_instance = lambda obj: get_user_display_name(obj)


class StrictLoginMixin:
    """
    确保所有管理视图都重定向到自定义登录页面
    现在由CustomAdminSite处理，这个mixin可以简化
    """
    pass

class CustomerAdmin(StrictLoginMixin, admin.ModelAdmin):
    form = CustomerAdminForm  # 使用自定义表单
    list_display = ['name', 'customer_type', 'status', 'contact_person', 'contact_phone', 'formatted_market_manager', 'formatted_service_manager', 'formatted_created_by', 'created_at']
    list_filter = ['customer_type', 'status', 'market_manager', 'service_manager']
    search_fields = ['name', 'contact_person', 'contact_phone', 'address']
    date_hierarchy = 'created_at'
    # 使用autocomplete_fields实现下拉选择市场经理和服务经理
    autocomplete_fields = ['market_manager', 'service_manager']
    list_per_page = 20  # 每页显示20条记录

    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，确保autocomplete显示姓名"""
        form = super().get_form(request, obj, **kwargs)
        # 为User外键字段添加label_from_instance来显示姓名
        if 'market_manager' in form.base_fields:
            def market_manager_label(user):
                return get_user_display_name(user)
            form.base_fields['market_manager'].label_from_instance = market_manager_label

        if 'service_manager' in form.base_fields:
            def service_manager_label(user):
                return get_user_display_name(user)
            form.base_fields['service_manager'].label_from_instance = service_manager_label

        return form

    def get_fieldsets(self, request, obj=None):
        """自定义字段分组"""
        if not obj:  # 添加页面
            return [
                ('基本信息', {
                    'fields': ('name', 'customer_type', 'status', 'contact_person', 'contact_phone')
                }),
                ('经理配置', {
                    'fields': ('market_manager', 'service_manager')
                }),
                ('地址信息', {
                    'fields': ('address',)
                }),
            ]
        else:  # 编辑页面
            return [
                ('基本信息', {
                    'fields': ('name', 'customer_type', 'status', 'contact_person', 'contact_phone')
                }),
                ('经理配置', {
                    'fields': ('market_manager', 'service_manager')
                }),
                ('地址信息', {
                    'fields': ('address',)
                }),
            ]

    def formatted_market_manager(self, obj):
        return get_user_display_name(obj.market_manager)
    formatted_market_manager.short_description = '市场经理'
    formatted_market_manager.admin_order_field = 'market_manager'

    def formatted_service_manager(self, obj):
        return get_user_display_name(obj.service_manager)
    formatted_service_manager.short_description = '服务经理'
    formatted_service_manager.admin_order_field = 'service_manager'

    def formatted_created_by(self, obj):
        return get_user_display_name(obj.created_by)
    formatted_created_by.short_description = '创建人'
    formatted_created_by.admin_order_field = 'created_by'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        return urls

    def has_view_permission(self, request, obj=None):
        """检查是否有查看权限"""
        if request.user.is_superuser:
            return True
        # 检查是否有查看客户的权限
        if request.user.has_perm('customers.view_customer'):
            return True
        return False

    def has_add_permission(self, request):
        """检查是否有添加权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('customers.add_customer')

    def has_change_permission(self, request, obj=None):
        """检查是否有修改权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('customers.change_customer')

    def has_delete_permission(self, request, obj=None):
        """检查是否有删除权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('customers.delete_customer')

    def save_model(self, request, obj, form, change):
        if not change:  # 新建时自动设置创建者
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class CustomerTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']


class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service_type', 'service_date', 'formatted_engineer', 'result']
    list_filter = ['service_type', 'service_date']
    search_fields = ['customer__name', 'description']
    date_hierarchy = 'service_date'
    raw_id_fields = ['customer', 'engineer']

    def formatted_engineer(self, obj):
        return get_user_name(obj.engineer)
    formatted_engineer.short_description = '工程师'
    formatted_engineer.admin_order_field = 'engineer'


# 手动注册所有模型到admin.site
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerTag, CustomerTagAdmin)
admin.site.register(ServiceHistory, ServiceHistoryAdmin)
