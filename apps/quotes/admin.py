from django.contrib import admin
from .models import QuoteTemplate, Quote, QuoteItem, PriceConfig, ProductSeries, QuoteProduct


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


@admin.register(ProductSeries)
class ProductSeriesAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


@admin.register(QuoteProduct)
class QuoteProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'series', 'repair_price', 'labor_fee', 'status', 'formatted_created_by', 'created_at']
    list_filter = ['status', 'series', 'created_at']
    search_fields = ['name']
    raw_id_fields = ['series', 'created_by']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'series', 'status')
        }),
        ('价格信息', {
            'fields': ('repair_price', 'labor_fee')
        }),
        ('其他', {
            'fields': ('description',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuoteTemplate)
class QuoteTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['is_active']
    raw_id_fields = ['created_by']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_no', 'name', 'parts_amount', 'labor_amount', 'total_amount', 'status', 'valid_until', 'formatted_created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['quote_no', 'name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['created_by']
    readonly_fields = ['quote_no', 'total_amount', 'created_at', 'updated_at']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'

    fields = (
        'name',
        ('parts_amount', 'labor_amount', 'total_amount'),
        ('valid_from', 'valid_until'),
        'status',
        'remark',
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ['quote', 'item_type', 'product', 'item_name', 'quantity', 'unit_price', 'total_price']
    list_filter = ['item_type']
    search_fields = ['item_name', 'quote__quote_no']
    raw_id_fields = ['quote', 'product']


@admin.register(PriceConfig)
class PriceConfigAdmin(admin.ModelAdmin):
    list_display = ['config_type', 'name', 'code', 'product', 'price', 'is_active']
    list_filter = ['config_type', 'is_active']
    search_fields = ['name', 'code']
    raw_id_fields = ['product']
