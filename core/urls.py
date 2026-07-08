"""
URL configuration for TianXiaoEr After-Sales Service Platform.
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods




@require_http_methods(["GET", "POST"])
def custom_logout(request):
    """自定义退出登录视图 - 支持GET和POST"""
    auth_logout(request)
    return redirect('/login/')


def login_view(request):
    """自定义登录视图 - 完全独立页面"""
    if request.user.is_authenticated:
        return redirect(request.GET.get('next', '/'))
    return auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=False,
        redirect_field_name='next'
    )(request)


urlpatterns = [
    # 独立登录页面（不使用 admin 命名空间）
    path('login/', login_view, name='login'),

    # Auth - 退出登录
    path('logout/', custom_logout, name='logout'),

    # Admin
    path('admin/', admin.site.urls),

    # Admin 退出（保持兼容）
    path('admin/logout/', custom_logout, name='admin_logout'),

    # 备用退出路径
    path('accounts/logout/', custom_logout),

    # API endpoints
    path('api/rbac/', include('apps.rbac.urls')),  # RBAC API
    path('api/customers/', include('apps.customers.urls')),
    path('api/faults/', include('apps.faults.urls')),
    path('api/repairs/', include('apps.repairs.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/logistics/', include('apps.logistics.urls')),
    path('api/quotes/', include('apps.quotes.urls')),
    path('api/workflows/', include('apps.workflows.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/ai/', include('apps.ai_assistant.urls')),
    path('api/sms/', include('apps.sms.urls')),
    path('api/user-management/', include('apps.user_management.urls')),
    path('api/system/', include('apps.system_management.urls')),
    
    # Web URLs
    path('', include('core.web_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
