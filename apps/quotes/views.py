from rest_framework import viewsets, status, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from .models import QuoteTemplate, Quote, QuoteItem, PriceConfig, ProductSeries, QuoteProduct
from .serializers import (
    QuoteTemplateSerializer, QuoteSerializer, QuoteItemSerializer,
    PriceConfigSerializer, ProductSeriesSerializer, QuoteProductSerializer
)


class CustomPagination(pagination.PageNumberPagination):
    """自定义分页类，支持动态页面大小"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def product_list_view(request):
    """产品管理页面"""
    return render(request, 'products/index.html')


class ProductSeriesViewSet(viewsets.ModelViewSet):
    """产品系列视图集"""

    serializer_class = ProductSeriesSerializer
    pagination_class = None  # 禁用分页，返回所有数据

    def get_queryset(self):
        queryset = ProductSeries.objects.all().order_by('name')
        # 支持 include_inactive 参数，用于管理页面显示所有系列
        include_inactive = self.request.query_params.get('include_inactive', None)
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset

    def perform_create(self, serializer):
        # 自动记录创建者，如果未登录则设为系统用户
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(created_by=user)

    def perform_update(self, serializer):
        serializer.save()


class QuoteProductViewSet(viewsets.ModelViewSet):
    """产品视图集"""

    queryset = QuoteProduct.objects.all().order_by('-created_at')
    serializer_class = QuoteProductSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        series_id = self.request.query_params.get('series_id', None)
        if series_id:
            queryset = queryset.filter(series_id=series_id)

        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(repair_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(repair_price__lte=max_price)

        min_labor = self.request.query_params.get('min_labor', None)
        max_labor = self.request.query_params.get('max_labor', None)
        if min_labor:
            queryset = queryset.filter(labor_fee__gte=min_labor)
        if max_labor:
            queryset = queryset.filter(labor_fee__lte=max_labor)

        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


class QuoteTemplateViewSet(viewsets.ModelViewSet):
    """报价模板视图集"""

    queryset = QuoteTemplate.objects.filter(is_active=True)
    serializer_class = QuoteTemplateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuoteViewSet(viewsets.ModelViewSet):
    """报价单视图集"""

    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class QuoteItemViewSet(viewsets.ModelViewSet):
    """报价明细视图集"""

    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer


class PriceConfigViewSet(viewsets.ModelViewSet):
    """价格配置视图集"""

    queryset = PriceConfig.objects.filter(is_active=True)
    serializer_class = PriceConfigSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        config_type = self.request.query_params.get('config_type', None)
        if config_type:
            queryset = queryset.filter(config_type=config_type)

        return queryset
