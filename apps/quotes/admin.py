from django.contrib import admin
from import_export.admin import ImportMixin, ExportMixin
from django.urls import path, reverse
from .models import QuoteTemplate, Quote, QuoteItem, PriceConfig, ProductSeries, QuoteProduct
from .resources import QuoteProductResource
from core.admin_utils import get_user_name


class ProductSeriesAdmin(admin.ModelAdmin):
    """产品系列管理"""
    list_display = ['name', 'description', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    raw_id_fields = ['created_by']
    list_per_page = 50  # 增加每页显示数量
    list_editable = ['is_active']  # 允许在列表中直接编辑启用状态

    def get_queryset(self, request):
        """确保显示所有数据，包括未启用的"""
        return super().get_queryset(request).all()

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


class QuoteProductAdmin(ImportMixin, ExportMixin, admin.ModelAdmin):
    """产品管理 Admin - 支持导入导出"""
    resource_class = QuoteProductResource
    change_list_template = 'admin/change_list.html'
    list_display = ['id', 'name', 'series', 'repair_price', 'labor_fee', 'status', 'formatted_created_by', 'created_at']
    list_filter = ['status', 'series', 'created_at']
    search_fields = ['name', 'series__name']
    raw_id_fields = ['created_by']
    autocomplete_fields = ['series']  # 使用自动完成选择器
    readonly_fields = ['id', 'created_at', 'updated_at']

    # 导入导出配置
    from_encoding = 'utf-8-sig'  # 支持 Excel 中文
    skip_admin_log = False  # 记录导入日志
    skip_failed = False  # 导入失败时停止

    def get_urls(self):
        """添加导入导出 URL"""
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_action), name='quotes_quoteproduct_import'),
            path('export/', self.admin_site.admin_view(self.export_action), name='quotes_quoteproduct_export'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """在列表页添加导入导出 URL"""
        extra_context = extra_context or {}
        extra_context['import_url'] = reverse('admin:quotes_quoteproduct_import')
        extra_context['export_url'] = reverse('admin:quotes_quoteproduct_export')
        return super().changelist_view(request, extra_context)

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


class QuoteTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'formatted_created_by', 'created_at']
    list_filter = ['is_active']
    raw_id_fields = ['created_by']

    def formatted_created_by(self, obj):
        return get_user_name(obj.created_by)
    formatted_created_by.short_description = '创建人'


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


class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ['quote', 'item_type', 'product', 'item_name', 'quantity', 'unit_price', 'total_price']
    list_filter = ['item_type']
    search_fields = ['item_name', 'quote__quote_no']
    raw_id_fields = ['quote', 'product']


class PriceConfigAdmin(admin.ModelAdmin):
    list_display = ['config_type', 'name', 'code', 'product', 'price', 'is_active']
    list_filter = ['config_type', 'is_active']
    search_fields = ['name', 'code']
    raw_id_fields = ['product']


# 手动注册所有模型到admin.site
admin.site.register(ProductSeries, ProductSeriesAdmin)
admin.site.register(QuoteProduct, QuoteProductAdmin)
admin.site.register(QuoteTemplate, QuoteTemplateAdmin)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(QuoteItem, QuoteItemAdmin)
admin.site.register(PriceConfig, PriceConfigAdmin)
