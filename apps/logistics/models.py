from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class LogisticsChannel(models.Model):
    """物流渠道"""

    name = models.CharField('渠道名称', max_length=100)
    code = models.CharField('渠道代码', max_length=20, unique=True)
    carrier = models.CharField('承运商', max_length=100)

    API_TYPE_CHOICES = [
        ('kuaidi100', '快递100'),
        ('kuaidi', '快递鸟'),
        ('tencent', '腾讯云'),
        ('tencent_market', '腾讯云市场'),
        ('custom', '自定义'),
    ]

    api_type = models.CharField('API类型', max_length=20, choices=API_TYPE_CHOICES, default='kuaidi100')
    api_config = models.JSONField('API配置', default=dict, blank=True, help_text='API Key等配置信息')

    # 腾讯云API配置字段
    app_id = models.CharField('App ID', max_length=100, blank=True, help_text='腾讯云API App ID')
    app_key = models.CharField('App Key', max_length=100, blank=True, help_text='腾讯云API App Key')
    secret_key = models.CharField('Secret Key', max_length=100, blank=True, help_text='腾讯云API Secret Key')
    api_url = models.CharField('API地址', max_length=200, default='https://api.express.sdk.tencent.com', blank=True)

    # 腾讯云市场API配置字段
    secret_id = models.CharField('Secret ID', max_length=200, blank=True, help_text='腾讯云市场API Secret ID')
    secret_key_market = models.CharField('Secret Key', max_length=200, blank=True, help_text='腾讯云市场API Secret Key')
    market_api_url = models.CharField('API地址', max_length=200, default='https://ap-beijing.cloudmarket-apigw.com/service-2r11e3tz/point-list', blank=True)

    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'logistics_channels'
        verbose_name = '物流渠道'
        verbose_name_plural = '物流渠道'

    def __str__(self):
        return self.name


class LogisticsRecord(models.Model):
    """物流记录"""

    TRACK_TYPE_CHOICES = [
        ('inbound', '收件'),
        ('outbound', '发件'),
    ]

    order_no = models.CharField('关联单号', max_length=50)
    track_no = models.CharField('物流单号', max_length=100)
    track_type = models.CharField('物流类型', max_length=20, choices=TRACK_TYPE_CHOICES)

    channel = models.ForeignKey(LogisticsChannel, on_delete=models.SET_NULL, null=True, blank=True, related_name='records')

    # 收/发货信息 - 简化发货人信息（与返修单关联）
    sender_name = models.CharField('发货人', max_length=100, blank=True)
    sender_phone = models.CharField('发货人电话', max_length=20, blank=True)
    sender_address = models.CharField('发货地址', max_length=200, blank=True)

    receiver_name = models.CharField('收货人', max_length=100, blank=True)
    receiver_phone = models.CharField('收货人电话', max_length=20, blank=True)
    receiver_address = models.CharField('收货地址', max_length=200, blank=True)

    # 状态
    status = models.CharField('物流状态', max_length=50, blank=True)
    is_delivered = models.BooleanField('是否已签收', default=False)
    is_completed = models.BooleanField('是否已完成', default=False, help_text='物流已完成，不再查询')

    # 查询控制
    last_query_time = models.DateTimeField('最后查询时间', null=True, blank=True)
    query_count_today = models.IntegerField('今日查询次数', default=0, help_text='今日已查询次数')
    query_date = models.DateField('查询日期', null=True, blank=True, help_text='当前查询日期')

    # 最新位置
    current_location = models.CharField('当前位置', max_length=200, blank=True)

    # 公众链接
    public_url = models.URLField('公众查询链接', blank=True)
    is_shared = models.BooleanField('对外分享', default=False, help_text='开启后可通过链接分享物流信息')

    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'logistics_records'
        verbose_name = '物流记录'
        verbose_name_plural = '物流记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_no} - {self.track_no}"

    def can_query_today(self):
        """检查今天是否还可以查询"""
        today = timezone.now().date()
        
        # 如果物流已完成，不能再查询
        if self.is_completed:
            return False
        
        # 查询日期不是今天或没有查询记录，可以查询
        if self.query_date != today or self.last_query_time is None:
            return True
        
        # 如果今天已经查询过，不能再查询
        return self.query_count_today < 1

    def record_query(self):
        """记录查询"""
        today = timezone.now().date()
        
        if self.query_date != today:
            # 如果日期不同，重置查询次数
            self.query_date = today
            self.query_count_today = 1
        else:
            # 同一天，增加查询次数
            self.query_count_today += 1
        
        self.last_query_time = timezone.now()
        self.save()


class LogisticsTrace(models.Model):
    """物流轨迹"""
    
    logistics = models.ForeignKey(LogisticsRecord, on_delete=models.CASCADE, related_name='traces')
    trace_time = models.DateTimeField('轨迹时间')
    location = models.CharField('地点', max_length=200)
    status = models.CharField('状态', max_length=100)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        db_table = 'logistics_traces'
        verbose_name = '物流轨迹'
        verbose_name_plural = '物流轨迹'
        ordering = ['trace_time']
    
    def __str__(self):
        return f"{self.logistics.track_no} - {self.trace_time}"
