from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.models import User
from .models import FaultCategory, FaultReport, FaultImage, FaultComment, Solution


def get_user_name(user):
    """获取用户的姓名，优先使用 first_name + last_name，否则使用 username"""
    if user is None:
        return '-'
    if user.first_name or user.last_name:
        name = f"{user.last_name}{user.first_name}".strip()
        if not name:
            name = f"{user.first_name} {user.last_name}".strip()
        return name
    return user.username


class FaultCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'created_at']
    list_filter = ['parent']
    search_fields = ['code', 'name']


class FaultReportAdminForm(forms.ModelForm):
    """故障上报表单"""
    fault_no = forms.CharField(label='故障单号', required=False, widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}))

    class Meta:
        model = FaultReport
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 根据模式处理字段
        if self.instance.pk:
            # 编辑模式
            self.fields['fault_no'].initial = self.instance.fault_no
        else:
            # 添加模式 - 移除不需要的字段
            remove_fields = ['fault_no', 'report_time', 'created_at', 'updated_at',
                            'assigned_to', 'assigned_time', 'resolve_time', 'created_by',
                            'source', 'remark', 'solution']
            for field in remove_fields:
                self.fields.pop(field, None)


from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

class StrictLoginMixin:
    """
    确保所有管理视图都重定向到自定义登录页面
    现在由CustomAdminSite处理，这个mixin可以简化
    """
    pass

class FaultReportAdmin(StrictLoginMixin, admin.ModelAdmin):
    form = FaultReportAdminForm
    list_display = ['fault_no', 'title', 'customer', 'formatted_priority', 'formatted_status', 'created_at']
    list_filter = ['status', 'priority', 'fault_category']
    search_fields = ['fault_no', 'title', 'equipment_sn', 'customer__name']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['customer']  # 使用弹出选择框选择客户
    raw_id_fields = ['assigned_to', 'created_by']
    list_per_page = 20  # 每页显示20条记录

    # 优先级排序值映射
    PRIORITY_VALUE = {
        'urgent': 4,   # 紧急
        'high': 3,     # 高
        'normal': 2,   # 普通
        'low': 1,      # 低
    }

    # 状态排序值映射（已解决和已关闭排在最后）
    STATUS_VALUE = {
        'pending': 1,      # 待处理
        'processing': 2,   # 处理中
        'resolved': 99,    # 已解决
        'closed': 100,     # 已关闭
    }

    def get_queryset(self, request):
        """自定义查询集，按优先级和状态排序"""
        qs = super().get_queryset(request)

        # 创建排序字段
        qs = qs.annotate(
            priority_sort=Case(
                *[When(priority=k, then=Value(v)) for k, v in self.PRIORITY_VALUE.items()],
                default=Value(0),
                output_field=IntegerField()
            ),
            status_sort=Case(
                *[When(status=k, then=Value(v)) for k, v in self.STATUS_VALUE.items()],
                default=Value(0),
                output_field=IntegerField()
            )
        )

        # 先按优先级降序，再按状态升序，最后按创建时间降序
        return qs.order_by('-priority_sort', 'status_sort', '-created_at')

    def formatted_priority(self, obj):
        """格式化优先级显示，带视觉强调"""
        priority_icons = {
            'urgent': {'icon': '🔴', 'class': 'priority-urgent', 'text': '紧急'},
            'high': {'icon': '🟠', 'class': 'priority-high', 'text': '高'},
            'normal': {'icon': '🟡', 'class': 'priority-normal', 'text': '普通'},
            'low': {'icon': '🟢', 'class': 'priority-low', 'text': '低'},
        }

        info = priority_icons.get(obj.priority, priority_icons['normal'])
        return format_html(
            '<span class="priority-badge {}">{} {}</span>',
            info['class'],
            info['icon'],
            info['text']
        )

    formatted_priority.short_description = '优先级'
    formatted_priority.admin_order_field = 'priority'

    def formatted_status(self, obj):
        """格式化状态显示，带视觉强调"""
        status_badges = {
            'pending': {'class': 'status-pending', 'text': '待处理'},
            'processing': {'class': 'status-processing', 'text': '处理中'},
            'resolved': {'class': 'status-resolved', 'text': '已解决'},
            'closed': {'class': 'status-closed', 'text': '已关闭'},
        }

        info = status_badges.get(obj.status, status_badges['pending'])
        return format_html(
            '<span class="status-badge {}">{}</span>',
            info['class'],
            info['text']
        )

    formatted_status.short_description = '状态'
    formatted_status.admin_order_field = 'status'

    def has_view_permission(self, request, obj=None):
        """检查是否有查看权限"""
        if request.user.is_superuser:
            return True
        # 检查是否有查看故障的权限
        if request.user.has_perm('faults.view_faultreport'):
            return True
        return False

    def has_add_permission(self, request):
        """检查是否有添加权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('faults.add_faultreport')

    def has_change_permission(self, request, obj=None):
        """检查是否有修改权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('faults.change_faultreport')

    def has_delete_permission(self, request, obj=None):
        """检查是否有删除权限"""
        if request.user.is_superuser:
            return True
        return request.user.has_perm('faults.delete_faultreport')

    def get_readonly_fields(self, request, obj=None):
        """只读字段 - 编辑模式下没有需要强制的只读字段"""
        return []

    def get_fieldsets(self, request, obj=None):
        """统一添加和编辑页面的字段"""
        if not obj:  # 添加页面
            return [
                ('故障信息', {
                    'fields': ('title', 'description')
                }),
                ('客户与设备', {
                    'fields': ('customer', 'equipment_sn', 'equipment_name', 'fault_category')
                }),
                ('上报信息', {
                    'fields': ('reporter_name', 'reporter_phone')
                }),
                ('状态信息', {
                    'fields': ('status', 'priority')
                }),
            ]
        else:  # 编辑页面
            return [
                ('故障信息', {
                    'fields': ('fault_no', 'title', 'description')
                }),
                ('客户与设备', {
                    'fields': ('customer', 'equipment_sn', 'equipment_name', 'fault_category')
                }),
                ('上报信息', {
                    'fields': ('reporter_name', 'reporter_phone')
                }),
                ('状态信息', {
                    'fields': ('status', 'priority')
                }),
                ('处理方案', {
                    'fields': ('solution',)
                }),
            ]

    def get_exclude(self, request, obj=None):
        """排除不需要的字段"""
        exclude = []
        if not obj:  # 添加页面 - 表单中已经处理了
            pass
        else:  # 编辑页面
            exclude = ['source', 'assigned_to', 'assigned_time', 'resolve_time',
                      'remark', 'created_by']
        return exclude

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class FaultImageAdmin(admin.ModelAdmin):
    list_display = ['fault', 'description', 'formatted_uploaded_by', 'uploaded_at']
    raw_id_fields = ['fault', 'uploaded_by']

    def formatted_uploaded_by(self, obj):
        return get_user_name(obj.uploaded_by)
    formatted_uploaded_by.short_description = '上传人'
    formatted_uploaded_by.admin_order_field = 'uploaded_by'


class FaultCommentAdmin(admin.ModelAdmin):
    list_display = ['fault', 'formatted_author', 'created_at']
    raw_id_fields = ['fault', 'author']

    def formatted_author(self, obj):
        return get_user_name(obj.author)
    formatted_author.short_description = '评论人'
    formatted_author.admin_order_field = 'author'
    raw_id_fields = ['fault', 'author']


class SolutionAdmin(admin.ModelAdmin):
    list_display = ['title', 'fault_category', 'use_count', 'success_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'fault_category']
    search_fields = ['title', 'description']
    raw_id_fields = ['fault_category', 'created_by']
    readonly_fields = ['created_at', 'updated_at']


# 手动注册所有模型到admin.site
admin.site.register(FaultCategory, FaultCategoryAdmin)
admin.site.register(FaultReport, FaultReportAdmin)
admin.site.register(FaultImage, FaultImageAdmin)
admin.site.register(FaultComment, FaultCommentAdmin)
admin.site.register(Solution, SolutionAdmin)
