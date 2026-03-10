from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Customer, CustomerTag, ServiceHistory


class CustomerSerializer(serializers.ModelSerializer):
    """客户序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CustomerTagSerializer(serializers.ModelSerializer):
    """客户标签序列化器"""
    
    class Meta:
        model = CustomerTag
        fields = '__all__'


class ServiceHistorySerializer(serializers.ModelSerializer):
    """服务历史序列化器"""
    
    engineer_name = serializers.CharField(source='engineer.username', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    
    class Meta:
        model = ServiceHistory
        fields = '__all__'
