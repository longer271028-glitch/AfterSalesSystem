from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowTypeViewSet, WorkflowInstanceViewSet, WorkflowTaskViewSet,
    OrganizationViewSet, RoleViewSet, UserProfileViewSet
)

router = DefaultRouter()
router.register(r'types', WorkflowTypeViewSet, basename='workflow-type')
router.register(r'instances', WorkflowInstanceViewSet, basename='workflow-instance')
router.register(r'tasks', WorkflowTaskViewSet, basename='workflow-task')
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'profiles', UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('', include(router.urls)),
]
