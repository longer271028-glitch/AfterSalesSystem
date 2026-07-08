from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import RepairOrder, RepairRecord, RepairPart
from core.admin_utils import get_user_name


class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ['repair_no', 'project', 'customer', 'fault_report', 'formatted_equipment_name', 'receive_quantity', 'status', 'quote_amount', 'formatted_created_by', 'created_at']
    list_filter = ['status', 'project', 'created_at']
    search_fields = ['repair_no', 'equipment_sn', 'equipment_name__name', 'customer__name', 'fault_report__fault_no', 'fault_report__title', 'project__name', 'project__project_no']
    date_hierarchy = 'created_at'
    raw_id_fields = ['created_by', 'project']  # project使用raw_id_fields
    autocomplete_fields = ['customer', 'fault_report', 'equipment_name', 'product']
    readonly_fields = ['repair_no', 'created_at', 'updated_at']
    change_form_template = 'admin/repairs/repairorder/change_form.html'
    list_per_page = 20  # 每页显示20条记录

    def formatted_equipment_name(self, obj):
        """格式化设备名称显示"""
        if obj.equipment_name:
            return obj.equipment_name.name
        return '-'
    formatted_equipment_name.short_description = '设备名称'
    formatted_equipment_name.admin_order_field = 'equipment_name__name'

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'
    formatted_created_by.admin_order_field = 'created_by'

    # 添加页面只显示必要字段
    add_fieldsets = (
        ('基本信息', {
            'fields': ('project', 'customer', 'fault_report')
        }),
        ('设备信息', {
            'fields': ('equipment_sn', 'equipment_name', 'receive_quantity', 'fault_description')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:  # 添加页面
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """新增后返回返修管理首页"""
        return HttpResponseRedirect(reverse('repairs'))

    def save_model(self, request, obj, form, change):
        if not change:  # 新建时自动设置创建者
            obj.created_by = request.user
            # 不在这里生成 repair_no，让模型的 save() 方法自动处理
        super().save_model(request, obj, form, change)


class RepairRecordAdmin(admin.ModelAdmin):
    list_display = ['repair', 'action', 'formatted_operator', 'operate_time']
    list_filter = ['action', 'operate_time']
    date_hierarchy = 'operate_time'
    raw_id_fields = ['repair', 'operator']

    def formatted_operator(self, obj):
        return get_user_name(obj.operator)
    formatted_operator.short_description = '操作人'
    formatted_operator.admin_order_field = 'operator'


class RepairPartAdmin(admin.ModelAdmin):
    list_display = ['repair', 'part_name', 'quantity', 'unit_price', 'total_price']
    raw_id_fields = ['repair']


# 手动注册所有模型到admin.site
admin.site.register(RepairOrder, RepairOrderAdmin)
admin.site.register(RepairRecord, RepairRecordAdmin)
admin.site.register(RepairPart, RepairPartAdmin)
