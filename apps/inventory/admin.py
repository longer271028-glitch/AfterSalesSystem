from django.contrib import admin
from django.contrib.auth.models import User
from .models import Product, ProductCategory, StockRecord, StockCheck, Warehouse


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


class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent']
    list_filter = ['parent']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'product_type', 'category', 'cost_price', 'sale_price', 'is_active']
    list_filter = ['product_type', 'is_active', 'category']
    search_fields = ['code', 'name', 'specification']
    raw_id_fields = ['category']


class StockRecordAdmin(admin.ModelAdmin):
    list_display = ['product', 'record_type', 'quantity', 'balance', 'formatted_operator', 'operate_time']
    list_filter = ['record_type', 'operate_time']
    search_fields = ['product__name', 'related_order_no']
    date_hierarchy = 'operate_time'
    raw_id_fields = ['product', 'operator']

    def formatted_operator(self, obj):
        return get_user_name(obj.operator)
    formatted_operator.short_description = '操作人'
    formatted_operator.admin_order_field = 'operator'


class StockCheckAdmin(admin.ModelAdmin):
    list_display = ['check_no', 'warehouse', 'status', 'formatted_operator', 'created_at']
    list_filter = ['status', 'warehouse']
    date_hierarchy = 'created_at'
    raw_id_fields = ['operator']

    def formatted_operator(self, obj):
        return get_user_name(obj.operator)
    formatted_operator.short_description = '操作人'
    formatted_operator.admin_order_field = 'operator'


class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'formatted_manager', 'is_active']
    list_filter = ['is_active']
    raw_id_fields = ['manager']

    def formatted_manager(self, obj):
        return get_user_name(obj.manager)
    formatted_manager.short_description = '管理员'
    formatted_manager.admin_order_field = 'manager'


# 手动注册所有模型到admin.site
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(StockRecord, StockRecordAdmin)
admin.site.register(StockCheck, StockCheckAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
