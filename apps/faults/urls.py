from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FaultCategoryViewSet, FaultReportViewSet, SolutionViewSet

router = DefaultRouter()
router.register(r'categories', FaultCategoryViewSet, basename='fault-category')
router.register(r'reports', FaultReportViewSet, basename='fault-report')
router.register(r'solutions', SolutionViewSet, basename='solution')

urlpatterns = [
    path('', include(router.urls)),
]
