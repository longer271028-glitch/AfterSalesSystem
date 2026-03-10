from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, CustomerTagViewSet, ServiceHistoryViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'tags', CustomerTagViewSet, basename='tag')
router.register(r'histories', ServiceHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
]
