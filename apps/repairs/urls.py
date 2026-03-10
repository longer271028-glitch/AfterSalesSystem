from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RepairOrderViewSet, RepairRecordViewSet, RepairPartViewSet
)

router = DefaultRouter()
router.register(r'orders', RepairOrderViewSet, basename='repair-order')
router.register(r'records', RepairRecordViewSet, basename='repair-record')
router.register(r'parts', RepairPartViewSet, basename='repair-part')

urlpatterns = [
    path('', include(router.urls)),
]
