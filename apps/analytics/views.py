from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.utils import timezone
from .models import Dashboard, ChartConfig, AlertRule, AlertRecord, ReportTemplate
from .serializers import (
    DashboardSerializer, ChartConfigSerializer,
    AlertRuleSerializer, AlertRecordSerializer, ReportTemplateSerializer
)


class DashboardViewSet(viewsets.ModelViewSet):
    """仪表盘视图集"""
    
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 公开或我的仪表盘
        if self.request.user.is_authenticated:
            queryset = queryset.filter(Q(is_public=True) | Q(created_by=self.request.user))
        else:
            queryset = queryset.filter(is_public=True)
        
        return queryset


class ChartConfigViewSet(viewsets.ModelViewSet):
    """图表配置视图集"""
    
    queryset = ChartConfig.objects.all()
    serializer_class = ChartConfigSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        dashboard_id = self.request.query_params.get('dashboard_id', None)
        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)
        
        data_source = self.request.query_params.get('data_source', None)
        if data_source:
            queryset = queryset.filter(data_source=data_source)
        
        return queryset


class AlertRuleViewSet(viewsets.ModelViewSet):
    """预警规则视图集"""
    
    queryset = AlertRule.objects.filter(is_active=True)
    serializer_class = AlertRuleSerializer


class AlertRecordViewSet(viewsets.ModelViewSet):
    """预警记录视图集"""
    
    queryset = AlertRecord.objects.all()
    serializer_class = AlertRecordSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        rule_type = self.request.query_params.get('rule_type', None)
        if rule_type:
            queryset = queryset.filter(rule__rule_type=rule_type)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        """处理预警"""
        alert = self.get_object()
        alert.status = 'handled'
        alert.handler = request.user
        alert.handle_time = timezone.now()
        alert.handle_remark = request.data.get('remark', '')
        alert.save()
        
        return Response(AlertRecordSerializer(alert).data)
    
    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        """忽略预警"""
        alert = self.get_object()
        alert.status = 'ignored'
        alert.save()
        
        return Response(AlertRecordSerializer(alert).data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """预警统计"""
        total = AlertRecord.objects.count()
        pending = AlertRecord.objects.filter(status='pending').count()
        handled = AlertRecord.objects.filter(status='handled').count()
        ignored = AlertRecord.objects.filter(status='ignored').count()
        
        by_type = AlertRecord.objects.values('rule__rule_type').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'pending': pending,
            'handled': handled,
            'ignored': ignored,
            'by_type': list(by_type),
        })


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """报表模板视图集"""

    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer


class DashboardStatsView(APIView):
    """控制台统计API"""

    def get(self, request):
        """获取控制台统计数据"""
        from apps.customers.models import Customer
        from apps.faults.models import FaultReport
        from apps.repairs.models import RepairOrder
        from apps.inventory.models import Product

        # 客户总数
        customer_count = Customer.objects.count()

        # 待处理故障数量 - 使用英文状态码
        pending_faults_count = FaultReport.objects.filter(status='pending').count()

        # 维修中数量 - 只计算 status='repairing'
        repairing_count = RepairOrder.objects.filter(status='repairing').count()

        # 库存预警数量 (当前库存小于最小库存)
        low_stock_count = 0
        for product in Product.objects.filter(is_active=True):
            if product.current_stock < product.min_stock:
                low_stock_count += 1

        # 最近故障 (最新5条)
        recent_faults = FaultReport.objects.order_by('-created_at')[:5].values(
            'id', 'fault_no', 'title', 'status'
        )

        # 最近返修 (最新5条)
        recent_repairs = RepairOrder.objects.order_by('-created_at')[:5].values(
            'id', 'repair_no', 'equipment_name', 'status'
        )

        return Response({
            'customer_count': customer_count,
            'pending_faults_count': pending_faults_count,
            'repairing_count': repairing_count,
            'low_stock_count': low_stock_count,
            'recent_faults': list(recent_faults),
            'recent_repairs': list(recent_repairs),
        })
