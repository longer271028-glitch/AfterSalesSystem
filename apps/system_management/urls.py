from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatabaseConfigViewSet, SystemConfigViewSet, settings_view

router = DefaultRouter()
router.register(r'database', DatabaseConfigViewSet, basename='database-config')
router.register(r'config', SystemConfigViewSet, basename='system-config')

urlpatterns = [
    path('', include(router.urls)),
]
