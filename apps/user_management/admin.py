from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserPermissions
from .forms import CustomUserCreationForm


# 修改 User.__str__ 方法，让 admin 下拉框显示姓名
def get_user_display_name(user):
    """获取用户显示名称，按优先级从多个表中获取"""
    # 1. 优先使用 UserPermissions.name (user_page_permissions 表)
    try:
        permissions = getattr(user, 'page_permissions', None)
        if permissions and permissions.name:
            return permissions.name
    except:
        pass

    # 2. 其次使用 rbac_user_profiles.name (rbac_user_profiles 表)
    try:
        rbac_profile = getattr(user, 'rbac_profile', None)
        if rbac_profile and rbac_profile.name:
            return rbac_profile.name
    except:
        pass

    # 3. 最后使用 Django User 的 first_name + last_name
    if user.first_name or user.last_name:
        name = f"{user.last_name}{user.first_name}".strip()
        if not name:
            name = f"{user.first_name} {user.last_name}".strip()
        return name

    return user.username

User.__str__ = get_user_display_name


class UserPermissionsInline(admin.StackedInline):
    """用户权限内联"""

    model = UserPermissions
    can_delete = False
    verbose_name_plural = '权限配置'
    fields = ('name', 'role', 'department', 'page_permissions', 'remark')
    extra = 0
    max_num = 1  # 最多只允许一个权限配置

    def get_form(self, request, obj=None, **kwargs):
        """确保所有字段都是可选的"""
        form = super().get_form(request, obj, **kwargs)
        # 让所有字段可选
        for field_name in ['name', 'role', 'department', 'page_permissions', 'remark']:
            if field_name in form.base_fields:
                form.base_fields[field_name].required = False
        return form


class UserAdmin(BaseUserAdmin):
    """自定义用户管理"""

    inlines = (UserPermissionsInline,)
    add_form = CustomUserCreationForm

    list_display = ('username', 'get_name', 'email', 'get_role', 'get_department', 'is_active', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'last_login')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # 字段配置
    def get_fieldsets(self, request, obj=None):
        # 添加和编辑用户页面显示一致的字段
        if not obj:  # 添加用户时
            return [
                (None, {'fields': ('username', 'email', 'password1', 'password2')}),
            ]
        else:  # 编辑用户时 - 去掉groups字段
            return [
                (None, {'fields': ('username', 'email', 'password', 'is_active', 'is_staff', 'is_superuser')}),
            ]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def get_autocomplete(self, request, term):
        """自定义autocomplete搜索结果，返回姓名"""
        from django.db.models import Q
        queryset = self.model.objects.filter(
            Q(username__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term)
        )
        # 返回带姓名的格式
        return queryset[:20]

    def get_autocomplete_results(self, request, term, model_admin, source_field):
        """
        自定义autocomplete搜索结果的显示文本
        """
        from django.db.models import Q
        queryset = self.model.objects.filter(
            Q(username__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term)
        )
        # 返回 (id, display_text) 格式的列表
        return [(obj.pk, get_user_display_name(obj)) for obj in queryset[:20]]

    # 添加用户时不显示inline
    def get_inline_instances(self, request, obj=None):
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def get_name(self, obj):
        """显示姓名"""
        if obj.first_name or obj.last_name:
            return f"{obj.last_name}{obj.first_name}".strip() or f"{obj.first_name} {obj.last_name}".strip()
        return obj.username
    get_name.short_description = '姓名'

    def get_role(self, obj):
        """显示角色"""
        permissions = getattr(obj, 'page_permissions', None)
        if permissions:
            return permissions.get_role_display()
        return '未设置'
    get_role.short_description = '角色'

    def get_department(self, obj):
        """显示部门"""
        permissions = getattr(obj, 'page_permissions', None)
        if permissions and permissions.department:
            return permissions.department
        return ''
    get_department.short_description = '部门'

    def save_model(self, request, obj, form, change):
        """保存用户"""
        super().save_model(request, obj, form, change)

        # 如果是新建用户，创建permissions记录
        if not change:
            UserPermissions.objects.get_or_create(user=obj)


class UserPermissionsAdmin(admin.ModelAdmin):
    """用户权限管理"""

    list_display = ('formatted_user', 'name', 'role', 'department', 'created_at')
    list_filter = ('role', 'department', 'created_at')
    search_fields = ('user__username', 'name')
    readonly_fields = ('created_at', 'updated_at')

    def formatted_user(self, obj):
        """显示用户姓名"""
        if obj.user:
            if obj.user.first_name or obj.user.last_name:
                name = f"{obj.user.last_name}{obj.user.first_name}".strip()
                if not name:
                    name = f"{obj.user.first_name} {obj.user.last_name}".strip()
                return name
            return obj.user.username
        return '-'
    formatted_user.short_description = '用户'

    fieldsets = (
        ('用户信息', {'fields': ('user', 'name', 'role', 'department')}),
        ('权限配置', {'fields': ('page_permissions',)}),
        ('其他信息', {'fields': ('remark', 'created_at', 'updated_at')}),
    )


# 替换默认的UserAdmin
# 先检查User是否已注册，如果没注册则先注册再替换
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass  # User未注册，直接继续
admin.site.register(User, UserAdmin)
admin.site.register(UserPermissions, UserPermissionsAdmin)


# 页面权限常量
PAGE_PERMISSIONS = [
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
    ('settings', '系统设置'),
]

