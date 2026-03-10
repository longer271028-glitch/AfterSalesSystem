from django.contrib import admin
from django.contrib.auth.models import User
from .models import RepairOrder, RepairRecord, RepairPart


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


class RepairOrderAdmin(admin.ModelAdmin):
    list_display = ['repair_no', 'customer', 'fault_report', 'equipment_name', 'equipment_sn', 'status', 'quote_amount', 'formatted_created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['repair_no', 'equipment_sn', 'equipment_name', 'customer__name', 'fault_report__fault_no', 'fault_report__title']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['customer', 'fault_report']  # 使用弹出选择框选择客户和故障单
    raw_id_fields = ['created_by']
    readonly_fields = ['repair_no', 'created_at', 'updated_at']
    change_form_template = 'admin/repairs/repairorder/change_form.html'
    list_per_page = 20  # 每页显示20条记录

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'
    formatted_created_by.admin_order_field = 'created_by'

    # 添加页面只显示必要字段
    add_fieldsets = (
        ('基本信息', {
            'fields': ('customer', 'fault_report')
        }),
        ('设备信息', {
            'fields': ('equipment_sn', 'equipment_name', 'receive_quantity', 'fault_description')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:  # 添加页面
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def save_model(self, request, obj, form, change):
        if not change:  # 新建时自动设置创建者
            obj.created_by = request.user
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
