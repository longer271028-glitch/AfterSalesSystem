from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet, ChartConfigViewSet, AlertRuleViewSet,
    AlertRecordViewSet, ReportTemplateViewSet, DashboardStatsView
)

router = DefaultRouter()
router.register(r'dashboards', DashboardViewSet, basename='dashboard')
router.register(r'charts', ChartConfigViewSet, basename='chart')
router.register(r'alerts', AlertRecordViewSet, basename='alert-record')
router.register(r'alert-rules', AlertRuleViewSet, basename='alert-rule')
router.register(r'reports', ReportTemplateViewSet, basename='report-template')

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
