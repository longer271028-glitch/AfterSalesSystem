from rest_framework import serializers
from .models import RepairOrder, RepairRecord, RepairPart
from apps.quotes.models import QuoteProduct


class RepairPartSerializer(serializers.ModelSerializer):
    """维修配件序列化器"""
    
    class Meta:
        model = RepairPart
        fields = '__all__'


class RepairRecordSerializer(serializers.ModelSerializer):
    """维修记录序列化器"""
    
    operator_name = serializers.CharField(source='operator.username', read_only=True)
    action_name = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = RepairRecord
        fields = '__all__'


class RepairOrderSerializer(serializers.ModelSerializer):
    """返修工单序列化器"""

    customer_name = serializers.SerializerMethodField()
    fault_report_title = serializers.SerializerMethodField()
    fault_report_no = serializers.SerializerMethodField()
    detect_person_name = serializers.CharField(source='detect_person.username', read_only=True)
    repair_person_name = serializers.CharField(source='repair_person.username', read_only=True)
    test_person_name = serializers.CharField(source='test_person.username', read_only=True)
    records = RepairRecordSerializer(many=True, read_only=True)
    parts = RepairPartSerializer(many=True, read_only=True)
    inbound_warehouse_name = serializers.CharField(source='inbound_warehouse.name', read_only=True)
    outbound_warehouse_name = serializers.CharField(source='outbound_warehouse.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    # 设备名称 - 返回产品名称字符串而不是ID
    equipment_name = serializers.StringRelatedField(read_only=True)
    # 设备名称ID - 用于编辑时关联
    equipment_name_id = serializers.PrimaryKeyRelatedField(
        source='equipment_name',
        queryset=QuoteProduct.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = RepairOrder
        fields = '__all__'
        read_only_fields = ('repair_no', 'created_at', 'updated_at')

    def get_customer_name(self, obj):
        return obj.customer.name if obj.customer else None

    def get_fault_report_title(self, obj):
        return obj.fault_report.title if obj.fault_report else None

    def get_fault_report_no(self, obj):
        return obj.fault_report.fault_no if obj.fault_report else None
