from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Count
from django.utils import timezone
from .models import FaultCategory, FaultReport, FaultImage, FaultComment, Solution
from .serializers import (
    FaultCategorySerializer, FaultReportSerializer, 
    FaultImageSerializer, FaultCommentSerializer, SolutionSerializer
)


class FaultCategoryViewSet(viewsets.ModelViewSet):
    """故障分类视图集"""

    queryset = FaultCategory.objects.filter(parent__isnull=True).order_by('code', 'id')
    serializer_class = FaultCategorySerializer


class FaultReportViewSet(viewsets.ModelViewSet):
    """故障上报视图集"""
    
    queryset = FaultReport.objects.all()
    serializer_class = FaultReportSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # 搜索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(fault_no__icontains=search) |
                Q(title__icontains=search) |
                Q(equipment_sn__icontains=search)
            )

        # 状态过滤
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # 优先级过滤
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)

        # 来源过滤
        source = self.request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source=source)

        # 客户过滤
        customer_id = self.request.query_params.get('customer_id', None)
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        # 添加默认排序
        queryset = queryset.order_by('-id')

        return queryset
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """分配故障"""
        fault = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        if not assigned_to_id:
            return Response({'error': '请指定处理人'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.contrib.auth.models import User
        try:
            assigned_to = User.objects.get(id=assigned_to_id)
            fault.assigned_to = assigned_to
            fault.assigned_time = timezone.now()
            fault.status = 'processing'
            fault.save()
            return Response(FaultReportSerializer(fault).data)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决故障"""
        fault = self.get_object()
        solution = request.data.get('solution', '')
        
        fault.solution = solution
        fault.status = 'resolved'
        fault.resolve_time = timezone.now()
        fault.save()
        
        return Response(FaultReportSerializer(fault).data)
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, pk=None):
        """添加故障图片"""
        fault = self.get_object()
        image = request.FILES.get('image')
        
        if not image:
            return Response({'error': '请上传图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        fault_image = FaultImage.objects.create(
            fault=fault,
            image=image,
            description=request.data.get('description', ''),
            uploaded_by=request.user
        )
        
        return Response(FaultImageSerializer(fault_image).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """添加备注"""
        fault = self.get_object()
        
        comment = FaultComment.objects.create(
            fault=fault,
            content=request.data.get('content', ''),
            author=request.user
        )
        
        return Response(FaultCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """故障统计"""
        total = FaultReport.objects.count()
        pending = FaultReport.objects.filter(status='pending').count()
        processing = FaultReport.objects.filter(status='processing').count()
        resolved = FaultReport.objects.filter(status='resolved').count()
        
        # 按故障类型统计
        by_category = FaultReport.objects.values('fault_category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 按优先级统计
        by_priority = FaultReport.objects.values('priority').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'pending': pending,
            'processing': processing,
            'resolved': resolved,
            'by_category': list(by_category),
            'by_priority': list(by_priority),
        })


class SolutionViewSet(viewsets.ModelViewSet):
    """解决方案视图集"""
    
    queryset = Solution.objects.filter(is_active=True)
    serializer_class = SolutionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        fault_category_id = self.request.query_params.get('fault_category_id', None)
        if fault_category_id:
            queryset = queryset.filter(fault_category_id=fault_category_id)

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # 添加默认排序
        queryset = queryset.order_by('-id')

        return queryset
    
    @action(detail=False, methods=['get'])
    def recommend(self, request):
        """推荐解决方案"""
        fault_category_id = request.query_params.get('fault_category_id')
        equipment_model = request.query_params.get('equipment_model')
        
        queryset = Solution.objects.filter(is_active=True)
        
        if fault_category_id:
            queryset = queryset.filter(fault_category_id=fault_category_id)
        
        if equipment_model:
            queryset = queryset.filter(
                Q(applicable_models__icontains=equipment_model) |
                Q(applicable_models='')
            )
        
        queryset = queryset.order_by('-use_count', '-success_rate')[:5]
        
        return Response(SolutionSerializer(queryset, many=True).data)
