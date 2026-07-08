from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, CustomerTag, ServiceHistory
from apps.user_management.admin import get_user_display_name


class CustomerSerializer(serializers.ModelSerializer):
    """客户序列化器"""

    created_by_name = serializers.SerializerMethodField()
    market_manager_name = serializers.SerializerMethodField()
    service_manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_created_by_name(self, obj):
        if obj.created_by:
            return get_user_display_name(obj.created_by)
        return None

    def get_market_manager_name(self, obj):
        if obj.market_manager:
            return get_user_display_name(obj.market_manager)
        return None

    def get_service_manager_name(self, obj):
        if obj.service_manager:
            return get_user_display_name(obj.service_manager)
        return None


class CustomerTagSerializer(serializers.ModelSerializer):
    """客户标签序列化器"""
    
    class Meta:
        model = CustomerTag
        fields = '__all__'


class ServiceHistorySerializer(serializers.ModelSerializer):
    """服务历史序列化器"""

    engineer_name = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = ServiceHistory
        fields = '__all__'

    def get_engineer_name(self, obj):
        if obj.engineer:
            return get_user_display_name(obj.engineer)
        return None
