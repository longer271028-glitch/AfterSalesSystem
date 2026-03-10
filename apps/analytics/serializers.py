from rest_framework import serializers
from .models import Dashboard, ChartConfig, AlertRule, AlertRecord, ReportTemplate


class ChartConfigSerializer(serializers.ModelSerializer):
    """图表配置序列化器"""
    
    class Meta:
        model = ChartConfig
        fields = '__all__'


class DashboardSerializer(serializers.ModelSerializer):
    """仪表盘序列化器"""
    
    charts = ChartConfigSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Dashboard
        fields = '__all__'


class AlertRuleSerializer(serializers.ModelSerializer):
    """预警规则序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AlertRule
        fields = '__all__'


class AlertRecordSerializer(serializers.ModelSerializer):
    """预警记录序列化器"""
    
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    handler_name = serializers.CharField(source='handler.username', read_only=True)
    
    class Meta:
        model = AlertRecord
        fields = '__all__'


class ReportTemplateSerializer(serializers.ModelSerializer):
    """报表模板序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ReportTemplate
        fields = '__all__'
