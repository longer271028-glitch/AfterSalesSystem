"""
Web URL configuration for Wuhan Hueda After-Sales System.
"""
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from apps.repairs.views import repair_list
from apps.quotes.views import product_list_view
from apps.quotes.api_views import import_export_view
from apps.sms.views import sms_management_view
from apps.user_management.views import permissions_management_view, users_management_view
from apps.system_management.views import settings_view
from apps.rbac.views import organization_management_view

urlpatterns = [
    path('', login_required(TemplateView.as_view(template_name='index.html')), name='home'),
    path('repairs/', login_required(repair_list), name='repairs'),
    # 产品管理页面 - 直接渲染模板
    path('products/', login_required(product_list_view), name='product-list'),
    # 产品导入导出工具页面
    path('products/import_export/', login_required(import_export_view), name='product-import-export'),
    # 产品API (使用 /api/quotes/ 前缀)
    path('api/quotes/', include(('apps.quotes.urls', 'quotes-api'), namespace='quotes-api')),
    path('inventory/', include(('apps.inventory.urls', 'inventory'), namespace='inventory')),
    path('logistics/', include(('apps.logistics.urls', 'logistics'), namespace='logistics')),
    # 手机短信管理
    path('sms/', login_required(sms_management_view), name='sms-management'),
    # 权限管理
    path('permissions/', login_required(permissions_management_view), name='permissions-management'),
    # 用户管理
    path('users/', login_required(users_management_view), name='users-management'),
    # 部门管理
    path('organization-management/', login_required(organization_management_view), name='organization-management'),
    # 系统设置
    path('settings/', login_required(settings_view), name='system-settings'),
]
