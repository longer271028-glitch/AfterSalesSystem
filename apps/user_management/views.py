from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserPermissions


def permissions_management_view(request):
    """权限管理页面"""
    # 检查是否登录
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')

    # 检查是否是管理员或有权限
    if not request.user.is_superuser and not request.user.has_perm('auth.change_user'):
        return render(request, 'user_management/unauthorized.html')

    return render(request, 'user_management/permissions.html')


def users_management_view(request):
    """用户管理页面"""
    # 检查是否登录
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')

    # 检查是否是管理员或有权限
    if not request.user.is_superuser and not request.user.has_perm('auth.change_user'):
        return render(request, 'user_management/unauthorized.html')

    return render(request, 'user_management/users.html')


class UserPermissionsViewSet(viewsets.ViewSet):
    """用户权限API"""

    # 页面权限常量
    PAGE_PERMISSIONS = [
        {'code': 'dashboard', 'name': '控制台'},
        {'code': 'customers', 'name': '客户管理'},
        {'code': 'faults', 'name': '故障管理'},
        {'code': 'repairs', 'name': '返修管理'},
        {'code': 'inventory', 'name': '库存管理'},
        {'code': 'logistics', 'name': '物流管理'},
        {'code': 'products', 'name': '产品管理'},
        {'code': 'sms', 'name': '手机短信'},
        {'code': 'analytics', 'name': '数据分析'},
        {'code': 'workflows', 'name': '流程引擎'},
        {'code': 'ai', 'name': 'AI助手'},
        {'code': 'settings', 'name': '系统设置'},
    ]

    def list(self, request):
        """获取所有用户及其权限"""
        users = User.objects.all().order_by('username')
        data = []
        for user in users:
            perms, created = UserPermissions.objects.get_or_create(user=user)
            data.append({
                'id': user.id,
                'username': user.username,
                'name': perms.name or '',
                'email': user.email or '',
                'role': perms.role,
                'role_display': perms.get_role_display(),
                'department': perms.department,
                'page_permissions': perms.page_permissions or [],
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            })
        return Response(data)

    @action(detail=False, methods=['get'])
    def pages(self, request):
        """获取所有页面权限选项"""
        return Response(self.PAGE_PERMISSIONS)

    @action(detail=True, methods=['post'])
    def add_permission(self, request, pk=None):
        """为用户添加页面权限"""
        try:
            user = User.objects.get(pk=pk)
            perms, created = UserPermissions.objects.get_or_create(user=user)
            page_code = request.data.get('page_code')
            
            if not page_code:
                return Response({'error': '缺少page_code参数'}, status=status.HTTP_400_BAD_REQUEST)
            
            if page_code not in perms.page_permissions:
                perms.page_permissions.append(page_code)
                perms.save()
            
            return Response({'success': True, 'page_permissions': perms.page_permissions})
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_permission(self, request, pk=None):
        """移除用户页面权限"""
        try:
            user = User.objects.get(pk=pk)
            perms, created = UserPermissions.objects.get_or_create(user=user)
            page_code = request.data.get('page_code')
            
            if not page_code:
                return Response({'error': '缺少page_code参数'}, status=status.HTTP_400_BAD_REQUEST)
            
            if page_code in perms.page_permissions:
                perms.page_permissions.remove(page_code)
                perms.save()
            
            return Response({'success': True, 'page_permissions': perms.page_permissions})
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def set_permissions(self, request, pk=None):
        """设置用户权限（覆盖）"""
        try:
            user = User.objects.get(pk=pk)
            perms, created = UserPermissions.objects.get_or_create(user=user)

            # 更新权限
            if 'page_permissions' in request.data:
                perms.page_permissions = request.data['page_permissions']
            if 'role' in request.data:
                perms.role = request.data['role']
            if 'department' in request.data:
                perms.department = request.data['department']
            if 'name' in request.data:
                perms.name = request.data['name']

            perms.save()

            return Response({
                'success': True,
                'page_permissions': perms.page_permissions,
                'role': perms.role,
                'department': perms.department,
                'name': perms.name,
            })
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """获取单个用户权限详情"""
        try:
            user = User.objects.get(pk=pk)
            perms, created = UserPermissions.objects.get_or_create(user=user)

            return Response({
                'id': user.id,
                'username': user.username,
                'name': perms.name or '',
                'email': user.email or '',
                'role': perms.role,
                'role_display': perms.get_role_display(),
                'department': perms.department,
                'page_permissions': perms.page_permissions or [],
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
            })
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
