from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductSeriesViewSet, QuoteProductViewSet, QuoteTemplateViewSet,
    QuoteViewSet, QuoteItemViewSet, PriceConfigViewSet
)

# API路由
router = DefaultRouter()
router.register(r'series', ProductSeriesViewSet, basename='product-series')
router.register(r'products', QuoteProductViewSet, basename='product')
router.register(r'templates', QuoteTemplateViewSet, basename='quote-template')
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'items', QuoteItemViewSet, basename='quote-item')
router.register(r'price-configs', PriceConfigViewSet, basename='price-config')

urlpatterns = [
    path('', include(router.urls)),
]