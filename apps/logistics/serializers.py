from rest_framework import serializers
from .models import LogisticsChannel, LogisticsRecord, LogisticsTrace


class LogisticsTraceSerializer(serializers.ModelSerializer):
    """物流轨迹序列化器"""
    
    class Meta:
        model = LogisticsTrace
        fields = '__all__'


class LogisticsRecordSerializer(serializers.ModelSerializer):
    """物流记录序列化器"""

    channel_name = serializers.CharField(source='channel.name', read_only=True)
    traces = LogisticsTraceSerializer(many=True, read_only=True)
    can_query_today = serializers.BooleanField(read_only=True)

    class Meta:
        model = LogisticsRecord
        fields = '__all__'


class LogisticsChannelSerializer(serializers.ModelSerializer):
    """物流渠道序列化器"""

    class Meta:
        model = LogisticsChannel
        fields = '__all__'
