from rest_framework import serializers
from .models import QuoteTemplate, Quote, QuoteItem, PriceConfig, ProductSeries, QuoteProduct


class ProductSeriesSerializer(serializers.ModelSerializer):
    """产品系列序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ProductSeries
        fields = '__all__'


class QuoteProductSerializer(serializers.ModelSerializer):
    """产品序列化器"""
    series_name = serializers.CharField(source='series.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = QuoteProduct
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, data):
        if 'labor_fee' in data and 'repair_price' in data:
            if data['labor_fee'] <= 0:
                raise serializers.ValidationError({'labor_fee': '维修工时费必须大于0'})
            if data['labor_fee'] > data['repair_price']:
                raise serializers.ValidationError({'labor_fee': '维修工时费不能大于维修价格'})
        return data


class QuoteItemSerializer(serializers.ModelSerializer):
    """报价明细序列化器"""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = QuoteItem
        fields = '__all__'


class QuoteSerializer(serializers.ModelSerializer):
    """报价单序列化器"""

    items = QuoteItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Quote
        fields = '__all__'
        read_only_fields = ('quote_no', 'created_at', 'updated_at')


class QuoteTemplateSerializer(serializers.ModelSerializer):
    """报价模板序列化器"""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = QuoteTemplate
        fields = '__all__'


class PriceConfigSerializer(serializers.ModelSerializer):
    """价格配置序列化器"""

    type_name = serializers.CharField(source='get_config_type_display', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = PriceConfig
        fields = '__all__'
