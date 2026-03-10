from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Customer, CustomerTag, ServiceHistory
from .serializers import CustomerSerializer, CustomerTagSerializer, ServiceHistorySerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """客户视图集"""
    
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # 搜索过滤
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(contact_phone__icontains=search)
            )

        # 类型过滤
        customer_type = self.request.query_params.get('customer_type', None)
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)

        # 状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 添加默认排序
        queryset = queryset.order_by('-id')

        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """客户统计"""
        total = Customer.objects.count()
        dealers = Customer.objects.filter(customer_type='dealer').count()
        terminals = Customer.objects.filter(customer_type='terminal').count()
        partners = Customer.objects.filter(customer_type='partner').count()
        
        return Response({
            'total': total,
            'dealers': dealers,
            'terminals': terminals,
            'partners': partners,
        })


class CustomerTagViewSet(viewsets.ModelViewSet):
    """客户标签视图集"""

    queryset = CustomerTag.objects.all().order_by('-id')
    serializer_class = CustomerTagSerializer


class ServiceHistoryViewSet(viewsets.ModelViewSet):
    """服务历史视图集"""

    queryset = ServiceHistory.objects.all().order_by('-service_date')
    serializer_class = ServiceHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        customer_id = self.request.query_params.get('customer_id', None)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        return queryset
