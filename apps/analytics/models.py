from django.db import models
from django.contrib.auth.models import User


class Dashboard(models.Model):
    """仪表盘"""
    
    name = models.CharField('仪表盘名称', max_length=100)
    code = models.CharField('仪表盘代码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    
    # 布局配置
    layout_config = models.JSONField('布局配置', default=dict)
    
    # 权限配置
    roles = models.ManyToManyField('workflows.Role', blank=True, related_name='dashboards')
    is_public = models.BooleanField('是否公开', default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_dashboards')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'dashboards'
        verbose_name = '仪表盘'
        verbose_name_plural = '仪表盘'
    
    def __str__(self):
        return self.name


class ChartConfig(models.Model):
    """图表配置"""
    
    CHART_TYPE_CHOICES = [
        ('line', '折线图'),
        ('bar', '柱状图'),
        ('pie', '饼图'),
        ('table', '表格'),
        ('gauge', '仪表盘'),
        ('scatter', '散点图'),
    ]
    
    name = models.CharField('图表名称', max_length=100)
    chart_type = models.CharField('图表类型', max_length=20, choices=CHART_TYPE_CHOICES)
    
    # 数据源配置
    data_source = models.CharField('数据源', max_length=100, 
        choices=[
            ('fault', '故障数据'),
            ('repair', '维修数据'),
            ('inventory', '库存数据'),
            ('customer', '客户数据'),
            ('quote', '报价数据'),
        ])
    query_config = models.JSONField('查询配置', default=dict)
    
    # 展示配置
    display_config = models.JSONField('展示配置', default=dict)
    
    # 所属仪表盘
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='charts', null=True, blank=True)
    
    # 位置
    x = models.IntegerField('X坐标', default=0)
    y = models.IntegerField('Y坐标', default=0)
    width = models.IntegerField('宽度', default=4)
    height = models.IntegerField('高度', default=3)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_charts')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'chart_configs'
        verbose_name = '图表配置'
        verbose_name_plural = '图表配置'
    
    def __str__(self):
        return self.name


class AlertRule(models.Model):
    """预警规则"""
    
    RULE_TYPE_CHOICES = [
        ('inventory', '库存预警'),
        ('repair', '维修周期预警'),
        ('fault', '故障预警'),
        ('quote', '报价预警'),
    ]
    
    name = models.CharField('规则名称', max_length=100)
    rule_type = models.CharField('规则类型', max_length=20, choices=RULE_TYPE_CHOICES)
    description = models.TextField('描述', blank=True)
    
    # 条件配置
    condition_config = models.JSONField('条件配置', default=dict)
    
    # 通知配置
    notify_config = models.JSONField('通知配置', default=dict)
    
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_alert_rules')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'alert_rules'
        verbose_name = '预警规则'
        verbose_name_plural = '预警规则'
    
    def __str__(self):
        return self.name


class AlertRecord(models.Model):
    """预警记录"""
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('handled', '已处理'),
        ('ignored', '已忽略'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='records')
    title = models.CharField('预警标题', max_length=200)
    content = models.TextField('预警内容')
    
    # 触发数据
    trigger_data = models.JSONField('触发数据', default=dict)
    
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 处理信息
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_alerts')
    handle_time = models.DateTimeField('处理时间', null=True, blank=True)
    handle_remark = models.TextField('处理备注', blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'alert_records'
        verbose_name = '预警记录'
        verbose_name_plural = '预警记录'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class ReportTemplate(models.Model):
    """报表模板"""
    
    name = models.CharField('模板名称', max_length=100)
    code = models.CharField('模板代码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    
    # 数据源
    data_source = models.CharField('数据源', max_length=100)
    query_config = models.JSONField('查询配置', default=dict)
    
    # 字段映射
    field_mapping = models.JSONField('字段映射', default=dict)
    
    # 导出配置
    export_config = models.JSONField('导出配置', default=dict)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_report_templates')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'report_templates'
        verbose_name = '报表模板'
        verbose_name_plural = '报表模板'
    
    def __str__(self):
        return self.name
