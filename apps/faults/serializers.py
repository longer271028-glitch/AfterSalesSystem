from rest_framework import serializers
from .models import FaultCategory, FaultReport, FaultImage, FaultComment, Solution


class FaultCategorySerializer(serializers.ModelSerializer):
    """故障分类序列化器"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = FaultCategory
        fields = '__all__'
    
    def get_children(self, obj):
        children = obj.children.all()
        return FaultCategorySerializer(children, many=True).data


class FaultImageSerializer(serializers.ModelSerializer):
    """故障图片序列化器"""
    
    class Meta:
        model = FaultImage
        fields = '__all__'


class FaultCommentSerializer(serializers.ModelSerializer):
    """故障备注序列化器"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = FaultComment
        fields = '__all__'


class FaultReportSerializer(serializers.ModelSerializer):
    """故障上报序列化器"""

    fault_category_name = serializers.CharField(source='fault_category.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    images = FaultImageSerializer(many=True, read_only=True)
    comments = FaultCommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = FaultReport
        fields = '__all__'
        read_only_fields = ('fault_no', 'created_at', 'updated_at')


class SolutionSerializer(serializers.ModelSerializer):
    """解决方案序列化器"""
    
    fault_category_name = serializers.CharField(source='fault_category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Solution
        fields = '__all__'
