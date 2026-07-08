from rest_framework import serializers
from .models import Phone, SmsRecord


class PhoneSerializer(serializers.ModelSerializer):
    """手机序列化器"""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    user_name_display = serializers.SerializerMethodField()
    sms_count = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_sms_count(self, obj):
        return obj.sms_records.count()

    def get_user_name_display(self, obj):
        """获取使用者姓名，优先使用关联用户的姓名"""
        if obj.user:
            return obj.user.name or obj.user.user.username
        return obj.user_name or ''

    def to_representation(self, instance):
        """返回数据时，user 字段返回显示名称而非 ID"""
        data = super().to_representation(instance)
        # user 字段返回显示名称
        data['user'] = self.get_user_name_display(instance)
        return data

    def to_internal_value(self, data):
        """处理前端传入的 user 字段（字符串而非 ID）"""
        # 复制数据避免修改原始数据
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        
        # 如果 user 字段是字符串，存储到 user_name 字段
        user_value = data.get('user')
        if user_value is not None:
            # 如果是字符串（前端传入的使用者姓名）
            if isinstance(user_value, str):
                data['user_name'] = user_value
                data['user'] = None  # 清空外键关联
            # 如果是数字（可能是 ID），尝试查找 UserProfile
            elif str(user_value).isdigit():
                try:
                    from apps.rbac.models import UserProfile
                    profile = UserProfile.objects.get(id=int(user_value))
                    data['user'] = profile.id
                    data['user_name'] = ''
                except UserProfile.DoesNotExist:
                    data['user'] = None
                    data['user_name'] = ''
        
        return super().to_internal_value(data)


class SmsRecordSerializer(serializers.ModelSerializer):
    """短信记录序列化器"""

    phone_name = serializers.CharField(source='phone.name', read_only=True)
    is_read_display = serializers.CharField(source='get_is_read_display', read_only=True)
    # 格式化时间为HH:MM格式，适配HTML time input
    received_time = serializers.TimeField(format='%H:%M')

    class Meta:
        model = SmsRecord
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
