from rest_framework import serializers
from .models import DatabaseConfig, SystemConfig


class DatabaseConfigSerializer(serializers.ModelSerializer):
    """数据库配置序列化器"""

    class Meta:
        model = DatabaseConfig
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def to_representation(self, instance):
        """隐藏密码"""
        data = super().to_representation(instance)
        if instance.mysql_password:
            data['mysql_password'] = '***' if instance.mysql_password else ''
        return data


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""

    class Meta:
        model = SystemConfig
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
