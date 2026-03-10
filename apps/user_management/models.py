from django.db import models
from django.contrib.auth.models import User


class UserPermissions(models.Model):
    """用户页面权限"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='page_permissions', verbose_name='用户')

    # 合并的姓名字段
    name = models.CharField('姓名', max_length=100, blank=True)

    # 角色配置
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('manager', '经理'),
        ('staff', '员工'),
        ('viewer', '访客'),
    ]
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='staff')

    # 部门信息
    department = models.CharField('部门', max_length=50, blank=True)

    # 页面权限（JSON格式存储）
    page_permissions = models.JSONField('页面权限', default=list, blank=True,
                                        help_text='用户可访问的页面列表')

    # 其他信息
    remark = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_page_permissions'
        verbose_name = '用户权限'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user.username}"

    def get_page_permissions_list(self):
        """获取页面权限列表"""
        if isinstance(self.page_permissions, list):
            return self.page_permissions
        elif isinstance(self.page_permissions, str):
            import json
            try:
                return json.loads(self.page_permissions)
            except:
                return []
        return []

    def has_page_permission(self, page_code):
        """检查是否有页面访问权限"""
        if self.user.is_superuser:
            return True
        return page_code in self.get_page_permissions_list()
