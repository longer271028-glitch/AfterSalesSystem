from django.apps import AppConfig
from django.contrib import admin


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'
    verbose_name = '库存管理'

    def ready(self):
        """应用就绪时自动注册模型到Admin"""
        from .models import Warehouse, StockRecord, StockCheck, WarehouseCategory
        from .admin import WarehouseAdmin, StockRecordAdmin, StockCheckAdmin, WarehouseCategoryAdmin
        
        # 注册到admin site
        if not admin.site.is_registered(Warehouse):
            admin.site.register(Warehouse, WarehouseAdmin)
        if not admin.site.is_registered(StockRecord):
            admin.site.register(StockRecord, StockRecordAdmin)
        if not admin.site.is_registered(StockCheck):
            admin.site.register(StockCheck, StockCheckAdmin)
        if not admin.site.is_registered(WarehouseCategory):
            admin.site.register(WarehouseCategory, WarehouseCategoryAdmin)
