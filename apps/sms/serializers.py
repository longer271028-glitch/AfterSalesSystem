from rest_framework import serializers
from .models import Phone, SmsRecord


class PhoneSerializer(serializers.ModelSerializer):
    """手机序列化器"""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    sms_count = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_sms_count(self, obj):
        return obj.sms_records.count()


class SmsRecordSerializer(serializers.ModelSerializer):
    """短信记录序列化器"""

    phone_name = serializers.CharField(source='phone.name', read_only=True)
    is_read_display = serializers.CharField(source='get_is_read_display', read_only=True)

    class Meta:
        model = SmsRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
