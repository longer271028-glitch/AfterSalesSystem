from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.admin_utils import get_user_display_name


# Monkey patch User.__str__ to display name in admin autocomplete
def custom_user_str(self):
    return get_user_display_name(self)

User.add_to_class('__str__', custom_user_str)


class UserAdmin(BaseUserAdmin):
    """自定义用户管理"""

    list_display = ('username', 'get_full_name', 'email', 'role_display', 'is_active', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'last_login')
    search_fields = ('username', 'get_full_name', 'email')

    # 合并姓名字段
    def get_fieldsets(self, request, obj=None):
        if obj:  # 编辑用户时
            fieldsets = [
                (_('基本信息'), {'fields': ('username', 'email', 'first_name', 'last_name')}),
                (_('个人信息'), {'fields': ('role', 'department', 'phone')}),
                (_('权限'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
                (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
            ]
        else:  # 新建用户时
            fieldsets = [
                (_('基本信息'), {'fields': ('username', 'password', 'first_name', 'last_name', 'email')}),
                (_('个人信息'), {'fields': ('role', 'department', 'phone')}),
                (_('权限'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
            ]
        return fieldsets

    # 添加字段
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role'),
        }),
    )

    def get_full_name(self, obj):
        """显示完整姓名"""
        return obj.get_full_name()
    get_full_name.short_description = '姓名'

    def role_display(self, obj):
        """显示角色"""
        return getattr(obj, 'role', '普通用户')
    role_display.short_description = '角色'

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)
        if obj:  # 编辑用户时
            readonly_fields.extend(['username', 'last_login', 'date_joined'])
        return readonly_fields

    def save_model(self, request, obj, form, change):
        """保存用户"""
        super().save_model(request, obj, form, change)


# 替换默认的UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# 页面权限配置
class PagePermission:
    """页面权限定义"""
    PAGES = [
        ('dashboard', '控制台'),
        ('customers', '客户管理'),
        ('faults', '故障管理'),
        ('repairs', '返修管理'),
        ('inventory', '库存管理'),
        ('logistics', '物流管理'),
        ('products', '产品管理'),
        ('sms', '手机短信'),
        ('analytics', '数据分析'),
        ('workflows', '流程引擎'),
        ('ai', 'AI助手'),
    ]

    @classmethod
    def get_all_pages(cls):
        """获取所有页面"""
        return cls.PAGES

    @classmethod
    def get_page_name(cls, page_code):
        """根据页面代码获取页面名称"""
        for code, name in cls.PAGES:
            if code == page_code:
                return name
        return page_code


# 为了演示，给User模型添加page_permissions字段（需要在实际项目中通过迁移添加）
# 这里我们使用profile的方式来管理额外字段
