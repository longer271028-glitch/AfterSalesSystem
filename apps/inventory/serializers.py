from rest_framework import serializers
from apps.quotes.models import QuoteProduct
from .models import StockRecord, StockCheck, StockCheckDetail, Warehouse, WarehouseCategory, InventoryTabConfig
from apps.user_management.admin import get_user_display_name


class WarehouseCategorySerializer(serializers.ModelSerializer):
    """仓库类别序列化器"""

    warehouse_count = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseCategory
        fields = '__all__'

    def get_warehouse_count(self, obj):
        return obj.warehouses.count()


class WarehouseSerializer(serializers.ModelSerializer):
    """仓库序列化器"""

    manager_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Warehouse
        fields = '__all__'

    def get_manager_name(self, obj):
        if obj.manager and obj.manager.name:
            return obj.manager.name
        return None


class InventoryTabConfigSerializer(serializers.ModelSerializer):
    """库存Tab配置序列化器"""

    tab_name = serializers.CharField(source='get_tab_key_display', read_only=True)

    class Meta:
        model = InventoryTabConfig
        fields = '__all__'


class StockCheckDetailSerializer(serializers.ModelSerializer):
    """盘点明细序列化器"""

    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = StockCheckDetail
        fields = '__all__'


class StockCheckSerializer(serializers.ModelSerializer):
    """库存盘点序列化器"""
    
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    details = StockCheckDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = StockCheck
        fields = '__all__'


class StockRecordSerializer(serializers.ModelSerializer):
    """库存记录序列化器"""

    product_name = serializers.CharField(source='product.name', read_only=True)
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockRecord
        fields = '__all__'
