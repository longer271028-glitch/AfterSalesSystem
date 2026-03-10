from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import connection
import pymysql
from .models import DatabaseConfig, SystemConfig
from .serializers import DatabaseConfigSerializer, SystemConfigSerializer


def settings_view(request):
    """系统设置页面"""
    # 检查是否登录
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')

    # 检查是否是超级管理员
    if not request.user.is_superuser:
        return render(request, 'system_management/unauthorized.html')

    return render(request, 'system_management/settings.html')


class DatabaseConfigViewSet(viewsets.ModelViewSet):
    """数据库配置视图"""

    queryset = DatabaseConfig.objects.all().order_by('-created_at')
    serializer_class = DatabaseConfigSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """测试数据库连接"""
        db_type = request.data.get('db_type', 'sqlite')
        
        if db_type == 'sqlite':
            try:
                connection.ensure_connection()
                return Response({
                    'success': True,
                    'message': 'SQLite连接成功'
                })
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'SQLite连接失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # MySQL连接测试
        try:
            host = request.data.get('mysql_host', 'localhost')
            port = int(request.data.get('mysql_port', 3306))
            user = request.data.get('mysql_user', '')
            password = request.data.get('mysql_password', '')
            database = request.data.get('mysql_database', '')
            
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                connect_timeout=5
            )
            conn.close()
            
            return Response({
                'success': True,
                'message': 'MySQL连接成功'
            })
        except pymysql.Error as e:
            return Response({
                'success': False,
                'message': f'MySQL连接失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'连接失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def init_database(self, request):
        """初始化数据库"""
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        User = get_user_model()
        results = {
            'migrations': False,
            'superuser': False,
            'permissions': False,
            'errors': []
        }
        
        try:
            # 执行迁移
            call_command('migrate', '--run-syncdb', verbosity=0)
            results['migrations'] = True
        except Exception as e:
            results['errors'].append(f'迁移失败: {str(e)}')
        
        try:
            # 创建超级管理员
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='123456'
                )
                results['superuser'] = True
            else:
                # 更新现有管理员密码
                admin_user = User.objects.get(username='admin')
                admin_user.set_password('123456')
                admin_user.save()
                results['superuser'] = True
        except Exception as e:
            results['errors'].append(f'创建超级管理员失败: {str(e)}')
        
        try:
            # 赋予所有权限
            admin_user = User.objects.get(username='admin')
            all_permissions = Permission.objects.all()
            admin_user.user_permissions.set(all_permissions)
            results['permissions'] = True
        except Exception as e:
            results['errors'].append(f'授权失败: {str(e)}')
        
        return Response(results)


class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置视图"""

    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def public_configs(self, request):
        """获取公开配置"""
        configs = SystemConfig.objects.filter(is_public=True)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)
