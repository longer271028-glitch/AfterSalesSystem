from django.db import models
from django.contrib.auth.models import User


class WorkflowType(models.Model):
    """流程类型"""
    
    name = models.CharField('流程名称', max_length=100)
    code = models.CharField('流程代码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    
    # 表单配置
    form_config = models.JSONField('表单配置', default=dict, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'workflow_types'
        verbose_name = '流程类型'
        verbose_name_plural = '流程类型'
    
    def __str__(self):
        return self.name


class WorkflowNode(models.Model):
    """流程节点"""
    
    NODE_TYPE_CHOICES = [
        ('start', '开始'),
        ('approval', '审批'),
        ('task', '任务'),
        ('condition', '条件'),
        ('end', '结束'),
    ]
    
    workflow = models.ForeignKey(WorkflowType, on_delete=models.CASCADE, related_name='nodes')
    name = models.CharField('节点名称', max_length=100)
    node_type = models.CharField('节点类型', max_length=20, choices=NODE_TYPE_CHOICES)
    
    # 审批/处理人配置
    assignee_type = models.CharField('处理人类型', max_length=20, default='role', 
        choices=[
            ('user', '指定用户'),
            ('role', '角色'),
            ('dept', '部门'),
            ('initiator', '申请人'),
        ])
    assignee_value = models.CharField('处理人值', max_length=100, blank=True)
    
    # 表单配置
    form_config = models.JSONField('节点表单配置', default=dict, blank=True)
    
    # 顺序
    order = models.IntegerField('顺序', default=0)
    
    # 超时配置
    timeout_hours = models.IntegerField('超时小时数', default=0)
    
    class Meta:
        db_table = 'workflow_nodes'
        verbose_name = '流程节点'
        verbose_name_plural = '流程节点'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.name}"


class WorkflowInstance(models.Model):
    """流程实例"""
    
    STATUS_CHOICES = [
        ('running', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('rejected', '已拒绝'),
    ]
    
    workflow = models.ForeignKey(WorkflowType, on_delete=models.CASCADE, related_name='instances')
    title = models.CharField('流程标题', max_length=200)
    
    # 业务关联
    business_type = models.CharField('业务类型', max_length=50, blank=True)
    business_id = models.CharField('业务ID', max_length=50, blank=True)
    
    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='running')
    current_node = models.ForeignKey(WorkflowNode, on_delete=models.SET_NULL, null=True, blank=True)
    
    # 申请人
    initiator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='initiated_workflows')
    
    # 表单数据
    form_data = models.JSONField('表单数据', default=dict, blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    class Meta:
        db_table = 'workflow_instances'
        verbose_name = '流程实例'
        verbose_name_plural = '流程实例'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.title}"


class WorkflowTask(models.Model):
    """流程任务"""
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('transferred', '已转交'),
    ]
    
    instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, related_name='tasks')
    node = models.ForeignKey(WorkflowNode, on_delete=models.CASCADE)
    
    # 处理人
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_tasks')
    
    # 状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 处理意见
    comment = models.TextField('处理意见', blank=True)
    
    # 时间
    assigned_at = models.DateTimeField('分配时间', auto_now_add=True)
    handled_at = models.DateTimeField('处理时间', null=True, blank=True)
    
    class Meta:
        db_table = 'workflow_tasks'
        verbose_name = '流程任务'
        verbose_name_plural = '流程任务'
    
    def __str__(self):
        return f"{self.instance.title} - {self.node.name}"


class Organization(models.Model):
    """组织单元"""
    
    name = models.CharField('组织名称', max_length=100)
    code = models.CharField('组织代码', max_length=50, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_depts')
    
    description = models.TextField('描述', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'organizations'
        verbose_name = '组织单元'
        verbose_name_plural = '组织单元'
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """角色"""
    
    name = models.CharField('角色名称', max_length=50)
    code = models.CharField('角色代码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    
    # 权限
    permissions = models.JSONField('权限', default=list, blank=True)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = '角色'
        verbose_name_plural = '角色'
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """用户扩展信息"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 组织信息
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    
    # 基本信息
    employee_no = models.CharField('员工工号', max_length=50, blank=True)
    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True)
    
    # 状态
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = '用户扩展信息'
        verbose_name_plural = '用户扩展信息'
    
    def __str__(self):
        return self.user.username
