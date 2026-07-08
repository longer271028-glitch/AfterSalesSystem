from django.db import models
from django.contrib.auth.models import User
from apps.customers.models import Customer
from apps.quotes.models import QuoteProduct


class FaultCategory(models.Model):
    """故障分类"""
    
    name = models.CharField('故障分类名称', max_length=100)
    code = models.CharField('故障代码', max_length=20, unique=True)
    description = models.TextField('描述', blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'fault_categories'
        verbose_name = '故障分类'
        verbose_name_plural = '故障分类'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class FaultReport(models.Model):
    """故障上报"""
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('resolved', '已解决'),
        ('closed', '已关闭'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    SOURCE_CHOICES = [
        ('customer', '客户上报'),
        ('service', '客服上报'),
        ('field', '现场人员上报'),
        ('system', '系统自动'),
    ]
    
    # 基本信息
    fault_no = models.CharField('故障单号', max_length=50, unique=True)
    title = models.CharField('故障标题', max_length=200)
    description = models.TextField('故障描述')
    
    # 关联信息
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='fault_reports', null=True, blank=True)
    equipment_sn = models.CharField('设备序列号', max_length=100, blank=True)
    equipment_name = models.ForeignKey(
        QuoteProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fault_reports',
        verbose_name='设备名称'
    )
    fault_category = models.ForeignKey(FaultCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='fault_reports')
    
    # 状态与优先级
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField('优先级', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    source = models.CharField('来源', max_length=20, choices=SOURCE_CHOICES, default='customer')
    
    # 上报信息
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='fault_reporter', verbose_name='上报人')
    reporter_name = models.CharField('上报人姓名（备用）', max_length=100, blank=True,
                                    help_text='用于外部人员上报，内部用户请关联到reporter字段')
    reporter_phone = models.CharField('上报人电话', max_length=20, blank=True)
    report_time = models.DateTimeField('上报时间', auto_now_add=True)
    
    # 处理信息
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_faults')
    assigned_time = models.DateTimeField('分配时间', null=True, blank=True)
    resolve_time = models.DateTimeField('解决时间', null=True, blank=True)
    solution = models.TextField('解决方案', blank=True)
    
    # 备注
    remark = models.TextField('备注', blank=True)
    
    # 创建信息
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_faults')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'fault_reports'
        verbose_name = '故障上报'
        verbose_name_plural = '故障上报'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.fault_no} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.fault_no:
            from django.utils import timezone
            from datetime import datetime
            date_str = timezone.now().strftime('%Y%m%d')
            count = FaultReport.objects.filter(fault_no__startswith=f'FT{date_str}').count() + 1
            self.fault_no = f'FT{date_str}{count:04d}'
        super().save(*args, **kwargs)


class FaultImage(models.Model):
    """故障图片"""
    
    fault = models.ForeignKey(FaultReport, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('图片', upload_to='faults/images/')
    description = models.CharField('描述', max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField('上传时间', auto_now_add=True)
    
    class Meta:
        db_table = 'fault_images'
        verbose_name = '故障图片'
        verbose_name_plural = '故障图片'


class FaultComment(models.Model):
    """故障备注/评论"""
    
    fault = models.ForeignKey(FaultReport, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField('内容')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'fault_comments'
        verbose_name = '故障备注'
        verbose_name_plural = '故障备注'
        ordering = ['created_at']


class Solution(models.Model):
    """解决方案库"""
    
    title = models.CharField('解决方案标题', max_length=200)
    fault_category = models.ForeignKey(FaultCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='solutions')
    description = models.TextField('解决方案描述')
    steps = models.TextField('解决步骤', blank=True, help_text='步骤用换行分隔')
    applicable_models = models.CharField('适用型号', max_length=500, blank=True, help_text='多个型号用逗号分隔')
    
    # 统计信息
    use_count = models.IntegerField('使用次数', default=0)
    success_rate = models.DecimalField('成功率', max_digits=5, decimal_places=2, default=0)
    
    # 状态
    is_active = models.BooleanField('是否启用', default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_solutions')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'solutions'
        verbose_name = '解决方案'
        verbose_name_plural = '解决方案'
        ordering = ['-use_count']
    
    def __str__(self):
        return self.title
