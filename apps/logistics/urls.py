from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import LogisticsChannelViewSet, LogisticsRecordViewSet

router = DefaultRouter()
router.register(r'channels', LogisticsChannelViewSet, basename='logistics-channel')
router.register(r'records', LogisticsRecordViewSet, basename='logistics-record')

urlpatterns = [
    # Web routes - placed before router to take precedence
    path('', views.logistics_unified, name='logistics-index'),
    path('channels/', views.logistics_channels, name='logistics-channels'),
    path('api/', include(router.urls)),
]
