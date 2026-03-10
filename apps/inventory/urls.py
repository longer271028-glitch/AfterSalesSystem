from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, StockRecordViewSet, StockCheckViewSet, WarehouseViewSet,
    WarehouseCategoryViewSet, InventoryTabConfigViewSet,
    inventory_list, warehouse_detail
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'stock', StockRecordViewSet, basename='stock')
router.register(r'checks', StockCheckViewSet, basename='stock-check')
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'warehouse-categories', WarehouseCategoryViewSet, basename='warehouse-category')
router.register(r'tab-configs', InventoryTabConfigViewSet, basename='tab-config')

urlpatterns = [
    path('api/', include(router.urls)),
    path('', inventory_list, name='index'),
    path('warehouse/<int:pk>/', warehouse_detail, name='warehouse_detail'),
]
