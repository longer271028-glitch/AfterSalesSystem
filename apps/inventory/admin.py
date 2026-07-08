from django.contrib import admin
from django.contrib.auth.models import User
from apps.rbac.models import UserProfile
from apps.quotes.models import QuoteProduct
from .models import StockRecord, StockCheck, StockCheckDetail, Warehouse, WarehouseCategory
from core.admin_utils import get_user_display_name


def get_product_display(product):
    """获取产品显示名称"""
    if product is None:
        return '-'
    return f"{product.name}"


class StockRecordAdmin(admin.ModelAdmin):
    """库存记录管理 - 出入库记录"""
    list_display = ['formatted_product', 'record_type', 'quantity', 'balance', 'formatted_warehouse', 'formatted_operator', 'operate_time']
    list_filter = ['record_type', 'operate_time', 'warehouse']
    search_fields = ['product__name', 'product__code', 'related_order_no']
    date_hierarchy = 'operate_time'
    # 使用 autocomplete_fields 实现产品下拉选择，确保出入库必须关联产品管理数据
    autocomplete_fields = ['product', 'warehouse']
    raw_id_fields = ['operator']

    def formatted_product(self, obj):
        return get_product_display(obj.product)
    formatted_product.short_description = '产品'
    formatted_product.admin_order_field = 'product__name'

    def formatted_warehouse(self, obj):
        return obj.warehouse.name if obj.warehouse else '-'
    formatted_warehouse.short_description = '仓库'
    formatted_warehouse.admin_order_field = 'warehouse__name'

    def formatted_operator(self, obj):
        return get_user_name(obj.operator)
    formatted_operator.short_description = '操作人'
    formatted_operator.admin_order_field = 'operator'


class StockCheckDetailInline(admin.TabularInline):
    """盘点明细内联 - 支持选择产品"""
    model = StockCheckDetail
    extra = 1
    # 使用 autocomplete_fields 实现产品下拉选择
    autocomplete_fields = ['product']
    fields = ['product', 'book_quantity', 'actual_quantity', 'difference', 'remark']
    readonly_fields = ['difference']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product')


class StockCheckAdmin(admin.ModelAdmin):
    """库存盘点管理"""
    list_display = ['check_no', 'warehouse', 'status', 'formatted_operator', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'warehouse']
    date_hierarchy = 'created_at'
    raw_id_fields = ['operator']
    inlines = [StockCheckDetailInline]

    def formatted_operator(self, obj):
        return get_user_name(obj.operator)
    formatted_operator.short_description = '操作人'
    formatted_operator.admin_order_field = 'operator'


class WarehouseCategoryAdmin(admin.ModelAdmin):
    """仓库类别管理"""
    list_display = ['name', 'code', 'sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['sort_order', 'id']


class WarehouseAdmin(admin.ModelAdmin):
    """仓库管理"""
    list_display = ['code', 'name', 'category', 'formatted_manager', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['code', 'name', 'address']
    autocomplete_fields = ['category']

    def get_form(self, request, obj=None, **kwargs):
        """自定义表单，确保manager下拉框显示姓名"""
        form = super().get_form(request, obj, **kwargs)
        if 'manager' in form.base_fields:
            # UserProfile 直接使用 name 字段显示
            form.base_fields['manager'].label_from_instance = lambda profile: profile.name if profile else ''
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制 manager 字段只能选择有效的 UserProfile"""
        if db_field.name == 'manager':
            from apps.rbac.models import UserProfile
            # 只显示有姓名的 UserProfile
            kwargs['queryset'] = UserProfile.objects.filter(
                name__isnull=False
            ).exclude(name='').order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formatted_manager(self, obj):
        return obj.name if obj.manager and obj.manager.name else '-'
    formatted_manager.short_description = '管理员'
    formatted_manager.admin_order_field = 'manager'


# 手动注册所有模型到admin.site
admin.site.register(StockRecord, StockRecordAdmin)
admin.site.register(StockCheck, StockCheckAdmin)
admin.site.register(WarehouseCategory, WarehouseCategoryAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
